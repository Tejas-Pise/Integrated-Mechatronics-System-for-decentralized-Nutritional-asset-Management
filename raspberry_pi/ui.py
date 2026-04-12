# ui.py — TFT touchscreen UI using pygame

import pygame
import sys
import time
import config

pygame.init()

W, H = config.TFT_WIDTH, config.TFT_HEIGHT

# Colors (government blue/green theme)
BG      = (10,  25,  60)
WHITE   = (255, 255, 255)
GREEN   = (0,   200, 100)
RED     = (220, 50,  50)
YELLOW  = (255, 210, 0)
BLUE    = (30,  100, 240)
GRAY    = (100, 110, 130)
DGRAY   = (40,  50,  70)
ORANGE  = (255, 130, 0)

FONT_BIG  = pygame.font.SysFont("dejavusans", 28, bold=True)
FONT_MED  = pygame.font.SysFont("dejavusans", 20)
FONT_SM   = pygame.font.SysFont("dejavusans", 14)

class KioskUI:
    def __init__(self):
        self.screen = pygame.display.set_mode(
            (W, H), pygame.FULLSCREEN if not __debug__ else 0
        )
        pygame.display.set_caption("Ration Kiosk")
        self.clock = pygame.time.Clock()

    def clear(self, color=BG):
        self.screen.fill(color)

    def header(self, title: str):
        pygame.draw.rect(self.screen, BLUE, (0, 0, W, 50))
        t = FONT_BIG.render(title, True, WHITE)
        self.screen.blit(t, (W//2 - t.get_width()//2, 10))

    def text(self, msg: str, y: int, color=WHITE, font=None):
        f = font or FONT_MED
        t = f.render(msg, True, color)
        self.screen.blit(t, (W//2 - t.get_width()//2, y))

    def button(self, label: str, x: int, y: int, w: int, h: int,
               color=GREEN) -> pygame.Rect:
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        t = FONT_MED.render(label, True, WHITE)
        self.screen.blit(t, (x + w//2 - t.get_width()//2,
                              y + h//2 - t.get_height()//2))
        return rect

    def progress_bar(self, label: str, y: int, pct: int, color=GREEN):
        self.text(label, y)
        bar_w = int((W - 80) * pct / 100)
        pygame.draw.rect(self.screen, DGRAY, (40, y+26, W-80, 20), border_radius=4)
        pygame.draw.rect(self.screen, color,  (40, y+26, bar_w,  20), border_radius=4)
        self.text(f"{pct}%", y+26, color, FONT_SM)

    def show_qr(self, pil_image, label: str = "Scan to Pay"):
        """Display UPI QR image (PIL Image) on screen."""
        import io
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        buf.seek(0)
        qr_surf = pygame.image.load(buf)
        qr_surf = pygame.transform.scale(qr_surf, (200, 200))
        self.screen.blit(qr_surf, (W//2 - 100, 80))
        self.text(label, 295, YELLOW)

    def flip(self):
        pygame.display.flip()
        self.clock.tick(30)

    def get_touch(self) -> tuple[int,int] | None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                return event.pos
            if event.type == pygame.FINGERDOWN:
                return (int(event.x * W), int(event.y * H))
        return None

    # ── Screens ──────────────────────────────────────────────

    def screen_welcome(self):
        self.clear()
        self.header("PDS Ration Kiosk")
        self.text("Government of India", 65, YELLOW)
        self.text("Scan RFID Card or", 120, WHITE)
        self.text("Enter Ration Card Number", 150, WHITE)
        btn = self.button("ENTER CARD NO.", 100, 200, 280, 50, BLUE)
        self.flip()
        return btn

    def screen_user_info(self, user: dict, quota: dict):
        self.clear()
        self.header("Citizen Details")
        self.text(f"Name: {user.get('name', 'N/A')}", 60, WHITE)
        self.text(f"Ration No: {user.get('ration_card', 'N/A')}", 90, WHITE)
        self.text(f"Scheme: {quota.get('scheme_type','N/A')}", 120, YELLOW)
        self.text(f"Family: {quota.get('family_size',1)} members", 150, WHITE)
        self.progress_bar(
            f"Quota: {quota['remaining_kg']:.1f} kg remaining",
            180,
            int(100 * quota['remaining_kg'] / max(quota['quota_kg'], 1)),
            GREEN
        )
        ok  = self.button("PROCEED",  60,  260, 160, 45, GREEN)
        no  = self.button("CANCEL",  260,  260, 160, 45, RED)
        self.flip()
        return ok, no

    def screen_grain_select(self, prices: dict) -> dict:
        """Show grain selection buttons. Returns button rect map."""
        self.clear()
        self.header("Select Grain Type")
        btns = {}
        grains = list(prices.keys())
        for i, g in enumerate(grains):
            x   = 20 + (i % 2) * 230
            y   = 70 + (i // 2) * 80
            lbl = f"{g.upper()}  ₹{prices[g]}/kg"
            btns[g] = self.button(lbl, x, y, 210, 55, BLUE)
        self.flip()
        return btns

    def screen_dispensing(self, grain: str, current: float, target: float):
        self.clear()
        self.header("Dispensing...")
        self.text(grain.upper(), 65, YELLOW, FONT_BIG)
        pct = min(100, int(100 * current / max(target, 0.01)))
        self.progress_bar(
            f"{current:.2f} kg / {target:.2f} kg",
            110, pct, GREEN
        )
        self.text("Please wait. Do not remove container.", 220, GRAY, FONT_SM)
        self.flip()

    def screen_done(self, grain: str, weight: float, amount: float, mode: str):
        self.clear()
        self.header("Transaction Complete")
        self.text(f"{grain.upper()} — {weight:.2f} kg", 80, GREEN, FONT_BIG)
        if mode == "FREE":
            self.text("FREE under govt scheme", 130, YELLOW)
        else:
            self.text(f"Amount Paid: ₹{amount:.2f}", 130, WHITE)
        self.text("Collect your ration. Thank you!", 175, WHITE)
        self.button("DONE", 180, 230, 120, 45, GREEN)
        self.flip()

    def screen_error(self, msg: str):
        self.clear()
        self.header("Error")
        self.text(msg, 120, RED)
        self.text("Please contact operator.", 160, WHITE)
        self.flip()

    def screen_fingerprint(self, attempt: int = 1):
        self.clear()
        self.header("Biometric Verification")
        self.text("Place finger on sensor", 100, WHITE, FONT_BIG)
        self.text(f"Attempt {attempt} of 3", 150, YELLOW)
        self.flip()

    def screen_payment(self, qr_img, amount: float, grain: str):
        self.clear()
        self.header("UPI Payment")
        self.show_qr(qr_img, f"Pay ₹{amount:.2f} for {grain}")
        btn_manual = self.button("CONFIRM PAYMENT", 130, 260, 220, 45, GREEN)
        btn_cancel  = self.button("CANCEL",          370, 260, 100, 45, RED)
        self.flip()
        return btn_manual, btn_cancel