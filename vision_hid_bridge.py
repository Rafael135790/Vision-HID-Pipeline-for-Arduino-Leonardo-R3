import hid
import dxcam
import cv2
import time
import random
import math
import traceback
import numpy as np
from collections import deque

# --- CONFIGURAÇÕES ---
VENDOR_ID, PRODUCT_ID, INTERFACE_ID = 0x3151, 0x402D, 0
FOV = 12
RADIUS = FOV // 2

# 🔥 CONTROLE DE ENVIO
SEND_INTERVAL = 0.001  # 250 Hz

# --- CONFIGS DE DEBUG/ESTABILIDADE ---
TARGET_FPS = 60                 # reduzir carga para debug
CAMERA_TIMEOUT_SEC = 2.0        # sem frame "novo" por 2s => reinicia câmera
HID_RECONNECT_DELAY = 1.0       # espera antes de tentar reconectar
STATUS_PRINT_EVERY = 2000       # imprime status a cada N frames
MAX_HID_ABS_MOVE = 20           # mantém seu clamp original

# --- MOTOR ---
class NeuroMotor:
    def __init__(self):
        self.session_state = 0.5
        self.tremor_x, self.tremor_y = 0.0, 0.0
        self.aggression = random.uniform(0.75, 0.95)
        self.speed_variation = 1.0
        self.acc_x, self.acc_y = 0.0, 0.0
        self.in_movement = False
        self.move_start_time = 0
        self.reaction_end = 0
        self.should_skip_current_target = False
        self.offset_x_jitter, self.offset_y_jitter = 0, 0
        self.drift_x, self.drift_y = 0.0, 0.0
        self.error_bias_x, self.error_bias_y = 0.0, 0.0
        self.control_state = 0.5
        self.history = deque(maxlen=120)
        self.hesitation = False
        self.commitment = 1.0
        self.planned_duration = 0.001

    def get_trend(self):
        if len(self.history) < 5:
            return 0, 0
        recent = list(self.history)[-5:]
        return sum(p[0] for p in recent) / 5, sum(p[1] for p in recent) / 5

    def update(self, dx, dy, is_new):
        now = time.perf_counter()
        self.history.append((dx, dy))
        self.session_state = max(0.0, min(1.0, self.session_state + random.uniform(-0.005, 0.005)))
        self.drift_x = (self.drift_x + random.uniform(-0.08, 0.08)) * 0.92
        self.drift_y = (self.drift_y + random.uniform(-0.08, 0.08)) * 0.92
        dist = math.hypot(dx, dy)

        if is_new:
            self.control_state = 0.7 * random.uniform(0, 1) + 0.3 * self.session_state
            self.should_skip_current_target = random.random() < (0.04 + self.control_state * 0.25)
            self.reaction_end = now + random.triangular(0.08, 0.15, 0.11)
            self.move_start_time = now
            self.planned_duration = max(
                0.001,
                (0.08 + 0.05 * math.log2(2 * dist / 5 + 1)) / self.aggression
            )
            self.in_movement = True

        if self.should_skip_current_target or now < self.reaction_end:
            return 0, 0

        tau = min(1.0, (now - self.move_start_time) / self.planned_duration)
        v_mult = 18.0 * (tau ** 1.2) * ((1 - tau) ** 2.0)
        mx = ((dx / self.planned_duration) * v_mult * 0.003 + (dx * (tau ** 3) * 0.25))
        my = ((dy / self.planned_duration) * v_mult * 0.003 + (dy * (tau ** 3) * 0.25))

        if tau >= 1.0:
            self.in_movement = False

        return mx, my

    def reset_target(self):
        self.should_skip_current_target = False
        self.in_movement = False
        self.acc_x, self.acc_y = 0.0, 0.0


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


# --- HID CONNECTION ---
def connect_hid(vid, pid, interface):
    h = hid.device()
    try:
        for dev in hid.enumerate():
            if (
                dev.get('vendor_id') == vid and
                dev.get('product_id') == pid and
                dev.get('interface_number', -1) == interface
            ):
                h.open_path(dev['path'])
                h.set_nonblocking(True)
                return h
        return None
    except Exception as e:
        log(f"[HID] erro ao enumerar/conectar: {repr(e)}")
        try:
            log(f"[HID] error(): {h.error()}")
        except Exception:
            pass
        try:
            h.close()
        except Exception:
            pass
        return None


def close_hid(h):
    if h is None:
        return
    try:
        h.close()
        log("[HID] handle fechado.")
    except Exception as e:
        log(f"[HID] erro ao fechar handle: {repr(e)}")


# --- DXCAM ---
def start_camera():
    log("3. Iniciando Captura de Tela (DXCam)...")
    cam = dxcam.create(max_buffer_len=64)
    left, top = (1920 - FOV) // 2, (1080 - FOV) // 2

    cam.start(
        region=(left, top, left + FOV, top + FOV),
        target_fps=TARGET_FPS,
        video_mode=True
    )

    log(f" -> DXCam iniciado na região central ({FOV}x{FOV}) com {TARGET_FPS} FPS e video_mode=True.")
    return cam


def stop_camera(cam):
    if cam is None:
        return
    try:
        cam.stop()
        log("[CAM] câmera parada.")
    except Exception as e:
        log(f"[CAM] erro ao parar câmera: {repr(e)}")


def get_latest_frame_safe(cam):
    """
    Tenta usar with_timestamp=True.
    Se a versão instalada do DXcam não suportar, cai no modo compatível.
    """
    try:
        frame, ts = cam.get_latest_frame(with_timestamp=True)
        return frame, ts
    except TypeError:
        frame = cam.get_latest_frame()
        return frame, time.perf_counter()
    except Exception:
        raise


# ==========================================
# INICIALIZAÇÃO
# ==========================================
print("1. Iniciando NeuroMotor...")
motor = NeuroMotor()

print("2. Conectando ao Arduino (HID)...")
arduino = connect_hid(VENDOR_ID, PRODUCT_ID, INTERFACE_ID)
if arduino:
    print(" -> HID CONECTADO COM SUCESSO!")
else:
    print(" -> AVISO: HID NÃO ENCONTRADO! Verifique cabo, firmware ou interface HID.")

try:
    camera = start_camera()
except Exception as e:
    print(f" -> ERRO CRÍTICO NO DXCAM: {e}")
    traceback.print_exc()
    input("Pressione ENTER para fechar...")
    raise SystemExit

_mask_circle = np.zeros((FOV, FOV), dtype=np.uint8)
cv2.circle(_mask_circle, (RADIUS, RADIUS), RADIUS, 255, -1)

target_locked = False
last_send_time = time.perf_counter()
frames_processados = 0

hid_writes_ok = 0
hid_write_failures = 0
hid_reconnects = 0

last_good_hid_write = time.perf_counter()
last_frame_received_perf = time.perf_counter()
last_frame_source_ts = 0.0
last_camera_restart = 0.0

print("=========================================")
print("4. TUDO PRONTO! SISTEMA RODANDO...")
print("=========================================")

# ==========================================
# LOOP PRINCIPAL
# ==========================================
try:
    while True:
        try:
            frame, frame_ts = get_latest_frame_safe(camera)
        except Exception as e:
            log(f"[CAM] erro ao obter frame: {repr(e)}")
            traceback.print_exc()
            stop_camera(camera)
            time.sleep(0.5)
            camera = start_camera()
            target_locked = False
            motor.reset_target()
            continue

        now_perf = time.perf_counter()

        if frame is None:
            # Evita spin quente se a captura vier vazia
            time.sleep(0.001)
            continue

        # Detecta se houve frame realmente "novo"
        if frame_ts != last_frame_source_ts:
            last_frame_source_ts = frame_ts
            last_frame_received_perf = now_perf

        # Watchdog da câmera: se o timestamp do frame não muda há muito tempo, reinicia
        if (now_perf - last_frame_received_perf > CAMERA_TIMEOUT_SEC) and (now_perf - last_camera_restart > 1.0):
            log(f"[CAM] mais de {CAMERA_TIMEOUT_SEC:.1f}s sem frame novo. Reiniciando câmera...")
            last_camera_restart = now_perf
            stop_camera(camera)
            time.sleep(0.2)
            camera = start_camera()
            target_locked = False
            motor.reset_target()
            continue

        frames_processados += 1
        if frames_processados % STATUS_PRINT_EVERY == 0:
            log(
                f"[STATUS] frames={frames_processados} | "
                f"hid_ok={hid_writes_ok} | "
                f"hid_fail={hid_write_failures} | "
                f"reconnects={hid_reconnects} | "
                f"ultimo_frame_novo_ha={now_perf - last_frame_received_perf:.3f}s | "
                f"ultimo_hid_ok_ha={now_perf - last_good_hid_write:.3f}s"
            )

        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, np.array([140, 85, 70]), np.array([160, 255, 255]))
        mask = cv2.bitwise_and(mask, mask, mask=_mask_circle)
        coords = cv2.findNonZero(mask)

        fx, fy = 0, 0

        if coords is not None and len(coords) > 6:
            top_pixel = coords[np.argmin(coords[:, :, 1])]
            cx, cy = top_pixel[0][0] - RADIUS, top_pixel[0][1] - RADIUS

            is_new = not target_locked
            target_locked = True

            if abs(cx) < 6 and cy < -2:
                mx, my = motor.update(cx, cy, is_new)
                motor.acc_x += mx
                motor.acc_y += my
                fx, fy = int(motor.acc_x), int(motor.acc_y)
                motor.acc_x -= fx
                motor.acc_y -= fy
        else:
            if target_locked:
                motor.reset_target()
            target_locked = False

        # --- SISTEMA DE HEARTBEAT E ENVIO ---
        if now_perf - last_send_time >= SEND_INTERVAL:
            last_send_time = now_perf

            if arduino:
                try:
                    move_x = max(-MAX_HID_ABS_MOVE, min(MAX_HID_ABS_MOVE, fx))
                    move_y = max(-MAX_HID_ABS_MOVE, min(MAX_HID_ABS_MOVE, fy))

                    payload = [0x00, move_x & 0xFF, move_y & 0xFF, 0x00] + [0] * 60
                    arduino.write(payload)

                    # Em nonblocking, isso deve retornar imediatamente
                    try:
                        arduino.read(64)
                    except Exception as re:
                        log(f"[HID] read falhou após write: {repr(re)}")

                    hid_writes_ok += 1
                    last_good_hid_write = now_perf

                except Exception as e:
                    hid_write_failures += 1
                    log(f"[HID] exceção no write/read: {repr(e)}")

                    try:
                        log(f"[HID] error(): {arduino.error()}")
                    except Exception as ee:
                        log(f"[HID] error() também falhou: {repr(ee)}")

                    close_hid(arduino)
                    arduino = None

                    time.sleep(HID_RECONNECT_DELAY)
                    arduino = connect_hid(VENDOR_ID, PRODUCT_ID, INTERFACE_ID)
                    hid_reconnects += 1

                    if arduino:
                        log("[HID] reconectado com sucesso.")
                    else:
                        log("[HID] reconexão falhou.")

            else:
                # Tenta recuperar sozinho se iniciou sem HID ou perdeu o dispositivo
                time.sleep(0.05)
                arduino = connect_hid(VENDOR_ID, PRODUCT_ID, INTERFACE_ID)
                if arduino:
                    hid_reconnects += 1
                    log("[HID] dispositivo encontrado novamente e reconectado.")

except KeyboardInterrupt:
    print("\nScript interrompido pelo usuário.")
except Exception as e:
    print(f"\nERRO NO LOOP: {e}")
    traceback.print_exc()
finally:
    print("\nDesligando câmera e fechando porta HID...")
    stop_camera(camera)
    close_hid(arduino)
    print("Programa finalizado com segurança.")
