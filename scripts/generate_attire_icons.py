from PIL import Image, ImageDraw
import os

OUT_DIR = "/Users/mac/ai-body-scan-saas/public/assets/attire-icons"
os.makedirs(OUT_DIR, exist_ok=True)

SIZE = 64

# Each attire: (id, name, bg_color, fg_color, shape)
attires = [
    # gho - Bhutanese robe
    ("gho", (200, 80, 60), (255, 200, 100), "robe"),
    # cheongsam - Chinese dress
    ("cheongsam", (200, 50, 50), (255, 215, 0), "cheongsam"),
    # shervani - Indian coat
    ("shervani", (180, 150, 100), (100, 80, 50), "shervani"),
    # sari - Indian draped
    ("sari", (160, 50, 120), (255, 200, 150), "sari"),
    # shalwar_kameez - Pakistani tunic
    ("shalwar_kameez", (50, 130, 80), (200, 220, 180), "shalwar"),
    # batik_kebaya - Indonesian
    ("batik_kebaya", (60, 100, 160), (200, 150, 100), "kebaya"),
    # bespoke_suit - custom suit
    ("bespoke_suit", (40, 50, 80), (180, 180, 190), "suit"),
    # savile_row - British tailoring
    ("savile_row", (30, 30, 50), (200, 200, 180), "suit"),
    # haute_couture - high fashion
    ("haute_couture", (20, 20, 30), (200, 180, 100), "gown"),
    # kilt - Scottish
    ("kilt", (180, 50, 50), (200, 180, 100), "kilt"),
    # thobe_kandura - Arabian robe
    ("thobe_kandura", (220, 215, 200), (180, 180, 170), "thobe"),
    # guayabera - Cuban shirt
    ("guayabera", (230, 225, 210), (100, 150, 180), "guayabera"),
    # bombachas - Gaucho trousers
    ("bombachas", (140, 100, 70), (200, 180, 140), "bombachas"),
    # gala - evening gown
    ("gala", (30, 30, 50), (220, 200, 180), "gown"),
    # suit - business suit
    ("suit", (50, 70, 110), (190, 200, 210), "suit"),
]

def draw_gown(draw, fg):
    draw.polygon([(20,12),(44,12),(48,28),(48,58),(44,60),(20,60),(16,58),(16,28)], fill=fg)
    draw.polygon([(24,12),(18,28),(46,28),(40,12)], fill=fg)
    draw.ellipse([(28,4),(36,12)], fill=fg)

def draw_suit(draw, fg):
    # Jacket body
    draw.polygon([(18,10),(46,10),(50,28),(50,56),(46,58),(18,58),(14,56),(14,28)], fill=fg)
    # Collar / lapels
    draw.polygon([(24,10),(18,28),(28,24)], fill=fg)
    draw.polygon([(40,10),(46,28),(36,24)], fill=fg)
    # V opening
    draw.polygon([(28,10),(36,10),(32,24)], fill=(min(fg[0]+30,255), min(fg[1]+30,255), min(fg[2]+30,255)))

def draw_robe(draw, fg):
    # knee-length robe
    draw.polygon([(16,6),(48,6),(52,56),(48,60),(16,60),(12,56)], fill=fg)
    # belt
    draw.rectangle([(12,30),(52,34)], fill=(min(fg[0]-30,0), min(fg[1]-30,0), min(fg[2]-30,0)))

def draw_cheongsam(draw, fg):
    # Fitted dress with slit
    draw.polygon([(22,6),(42,6),(48,30),(48,58),(44,60),(34,60),(34,48),(30,48),(30,60),(20,60),(16,58),(16,30)], fill=fg)
    # Mandarin collar
    draw.rectangle([(24,2),(40,8)], fill=fg)
    # Slit detail
    draw.line([(32,48),(32,60)], fill=(0,0,0), width=1)

def draw_shervani(draw, fg):
    # Long coat
    draw.polygon([(18,6),(46,6),(50,56),(46,60),(18,60),(14,56)], fill=fg)
    # Buttons
    for y in range(18, 50, 8):
        draw.ellipse([(30,y),(34,y+4)], fill=(min(fg[0]-40,0), min(fg[1]-40,0), min(fg[2]-40,0)))

def draw_sari(draw, fg):
    # Draped body
    draw.polygon([(20,4),(44,4),(48,56),(44,60),(20,60),(16,56)], fill=fg)
    # Pallu (draped over shoulder)
    draw.polygon([(14,4),(22,4),(26,36),(18,36)], fill=(min(fg[0]+40,255), min(fg[1]+40,255), min(fg[2]+40,255)))

def draw_shalwar(draw, fg):
    # Kameez (tunic)
    draw.polygon([(18,4),(46,4),(50,40),(46,44),(38,44),(36,52),(28,52),(26,44),(18,44),(14,40)], fill=fg)
    # Shalwar (trousers)
    draw.polygon([(26,44),(28,52),(22,60),(18,60),(14,52),(18,44)], fill=(fg[0]-20, fg[1]-20, fg[2]-20))
    draw.polygon([(38,44),(36,52),(42,60),(46,60),(50,52),(46,44)], fill=(fg[0]-20, fg[1]-20, fg[2]-20))

def draw_kebaya(draw, fg):
    # Kebaya blouse
    draw.polygon([(20,4),(44,4),(48,36),(44,40),(20,40),(16,36)], fill=fg)
    # Batik sarong (skirt)
    draw.polygon([(18,36),(46,36),(48,58),(44,60),(20,60),(16,58)], fill=(fg[0]+30, fg[1]+30, fg[2]-20))
    # Kebaya开放 front
    draw.polygon([(28,4),(36,4),(32,20)], fill=(0,0,0,0) if 0 else fg)

def draw_kilt(draw, fg):
    # Kilt (pleated skirt)
    for x in range(14, 50, 4):
        draw.line([(x,28),(x,58)], fill=fg, width=2)
    # Jacket top
    draw.polygon([(18,4),(46,4),(50,28),(46,30),(18,30),(14,28)], fill=(fg[0]-40, fg[1]-40, fg[2]-40))
    # Sporran
    draw.rectangle([(28,30),(36,40)], fill=(100,80,60))
    # Belt
    draw.rectangle([(14,26),(50,30)], fill=(80,70,50))

def draw_thobe(draw, fg):
    # Long white robe
    draw.polygon([(16,4),(48,4),(52,56),(48,60),(16,60),(12,56)], fill=fg)
    # Collar
    draw.polygon([(28,4),(36,4),(32,12)], fill=(fg[0]-20, fg[1]-20, fg[2]-20))

def draw_guayabera(draw, fg):
    # Guayabera shirt (untucked)
    draw.polygon([(18,4),(46,4),(50,56),(46,60),(18,60),(14,56)], fill=fg)
    # Pockets
    draw.rectangle([(16,20),(26,32)], fill=None, outline=(fg[0]-40, fg[1]-40, fg[2]-40))
    draw.rectangle([(38,20),(48,32)], fill=None, outline=(fg[0]-40, fg[1]-40, fg[2]-40))
    # Pintucks (vertical lines)
    for x in range(22, 42, 4):
        draw.line([(x,8),(x,18)], fill=(fg[0]-30, fg[1]-30, fg[2]-30), width=1)

def draw_bombachas(draw, fg):
    # Gaucho trousers - wide top, tapered ankle
    draw.polygon([(14,8),(50,8),(54,30),(50,34),(42,34),(38,56),(34,60),(30,60),(26,56),(22,34),(14,34),(10,30)], fill=fg)
    # Belt / faja
    draw.rectangle([(14,8),(50,12)], fill=(fg[0]-30, fg[1]-30, fg[2]-30))
    # Boots
    draw.rectangle([(26,56),(34,60)], fill=(80,60,40))
    draw.rectangle([(30,56),(34,60)], fill=(80,60,40))

shape_funcs = {
    "gown": draw_gown,
    "suit": draw_suit,
    "robe": draw_robe,
    "cheongsam": draw_cheongsam,
    "shervani": draw_shervani,
    "sari": draw_sari,
    "shalwar": draw_shalwar,
    "kebaya": draw_kebaya,
    "kilt": draw_kilt,
    "thobe": draw_thobe,
    "guayabera": draw_guayabera,
    "bombachas": draw_bombachas,
}

results = []
for attire_id, bg, fg, shape in attires:
    img = Image.new("RGBA", (SIZE, SIZE), bg + (255,))
    draw = ImageDraw.Draw(img)
    shape_funcs[shape](draw, fg)
    path = os.path.join(OUT_DIR, f"{attire_id}.png")
    img.save(path, "PNG")
    results.append((attire_id, "SUCCESS"))
    print(f"Created {attire_id}.png ({bg[0]},{bg[1]},{bg[2]})")

# Summary
print("\n--- SUMMARY ---")
for rid, status in results:
    print(f"  {rid}: {status}")
