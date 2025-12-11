import os, sys, random, time, pygame

def get_story_with_tkinter(default_text):
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        data = {"story": None}

        def submit():
            txt = text_box.get("1.0", tk.END).strip()
            data["story"] = txt if txt else None
            root.destroy()

        root = tk.Tk()
        root.title("StoryToGame — Enter your story")
        root.geometry("540x220")
        try:
            root.iconbitmap(False)
        except Exception:
            pass

        lbl = tk.Label(root, text="Type a short story for the game (press Start):", font=("Arial", 11))
        lbl.pack(padx=10, pady=(10, 6))

        text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=6, font=("Arial", 10))
        text_box.insert("1.0", default_text)
        text_box.pack(padx=10, pady=(0, 8))

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=(0,10))
        start_btn = tk.Button(btn_frame, text="Start Game", command=submit, width=12)
        start_btn.pack(side="left", padx=8)

        cancel_btn = tk.Button(btn_frame, text="Cancel (use terminal)", command=lambda: root.destroy(), width=16)
        cancel_btn.pack(side="left", padx=8)

        root.update_idletasks()
        w = root.winfo_width(); h = root.winfo_height()
        ws = root.winfo_screenwidth(); hs = root.winfo_screenheight()
        x = (ws // 2) - (w // 2); y = (hs // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")

        root.mainloop()
        return data["story"]
    except Exception as e:
        return None

DEFAULT_STORY = "A knight walks through the forest, later crosses a desert and finds a tomb."

story = get_story_with_tkinter(DEFAULT_STORY)
if story is None:
    try:
        story = input("Enter your story (press Enter for default): ").strip()
    except Exception:
        story = ""
if not story:
    story = DEFAULT_STORY
story_l = story.lower()

MODEL_PATH = "story_model.joblib"
VECT_PATH = "vectorizer.joblib"
model = None
vect = None
use_model = False
model_label_names = None

try:
    import joblib
    if os.path.exists(MODEL_PATH) and os.path.exists(VECT_PATH):
        model = joblib.load(MODEL_PATH)
        vect = joblib.load(VECT_PATH)
        use_model = True
        print("Loaded ML model & vectorizer.")
        try:
            if hasattr(model, "classes_"):
                model_label_names = list(getattr(model, "classes_"))
                print("Model.classes_ found:", model_label_names)
            elif hasattr(model, "estimators_"):
                names = []
                for est in getattr(model, "estimators_"):
                    if hasattr(est, "classes_"):
                        names.append(list(est.classes_))
                    else:
                        names.append(None)
                model_label_names = names
                print("Model estimators classes found.")
            else:
                print("No label metadata found inside model.")
        except Exception as e:
            print("Could not inspect model labels:", e)
    else:
        print("Model/vectorizer not found; using keyword fallback.")
except Exception as e:
    print("joblib/sklearn not available or failed to load model:", e)
    use_model = False

SPACE_KEYWORDS = ["space", "alien", "ship", "spaceship", "galaxy", "asteroid", "planet", "nebula", "ufo", "mothership"]

def keyword_override_space(s):
    return any(k in s for k in SPACE_KEYWORDS)

def choose_mode_from_model_safe(story_text):
    if not use_model or model is None or vect is None:
        return None
    try:
        X = vect.transform([story_text])
        pred = model.predict(X)
        print("Raw model output:", repr(pred))
        if hasattr(pred, "__len__") and not hasattr(pred[0], "__len__"):
            first = pred[0]
            fs = str(first).lower()
            if "space" in fs or "alien" in fs or "ship" in fs:
                return "space"
            return "knight"
        import numpy as _np
        arr = _np.array(pred)
        if arr.ndim == 2 and arr.shape[0] >= 1:
            vec = arr[0]
            if model_label_names and isinstance(model_label_names, list) and all(isinstance(x, str) for x in model_label_names) and len(model_label_names) == len(vec):
                chosen = [model_label_names[i] for i,v in enumerate(vec) if int(v)]
                print("Mapped labels from model:", chosen)
                if any("space" in c.lower() or "alien" in c.lower() or "ship" in c.lower() for c in chosen):
                    return "space"
                return "knight"
            if vec.sum() == 0:
                return None
            print("Model returned numeric vector but mapping unknown -> fallback to keywords.")
            return None
    except Exception as e:
        print("Model inference error:", e)
        return None
    return None

if keyword_override_space(story_l):
    chosen_mode = "space"
    print("Keyword override selected SPACE mode.")
else:
    mc = choose_mode_from_model_safe(story)
    if mc:
        chosen_mode = mc
        print("Chosen by model:", chosen_mode)
    else:
        chosen_mode = "knight"
        print("Falling back to KNIGHT mode (no strong model decision).")

pygame.init()
WIDTH, HEIGHT = 960, 540
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("StoryToGame - Final")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 24)

ASSETS_DIR = "assets"
GROUND_Y = HEIGHT - 72

def asset_path(subfolder, name):
    return os.path.join(ASSETS_DIR, subfolder, name)

def exists(subfolder, name):
    return os.path.exists(asset_path(subfolder, name))

def load_image(subfolder, name, fallback_size=(64,64), fallback_color=(80,80,80)):
    p = asset_path(subfolder, name)
    if os.path.exists(p):
        try:
            return pygame.image.load(p).convert_alpha()
        except Exception as e:
            print("Error loading image", p, e)
    s = pygame.Surface(fallback_size, pygame.SRCALPHA); s.fill(fallback_color)
    return s

castle_path = asset_path("knight", "castle.png")
if not os.path.exists(castle_path):
    try:
        print("Castle not found — creating placeholder at", castle_path)
        os.makedirs(os.path.dirname(castle_path), exist_ok=True)
        surf = pygame.Surface((120, 160), pygame.SRCALPHA)
        surf.fill((50,60,80))
        pygame.draw.rect(surf, (140,140,160), (12,60,96,88))
        pygame.draw.rect(surf, (100,100,120), (22,30,24,40))
        pygame.draw.rect(surf, (100,100,120), (74,30,24,40))
        pygame.draw.rect(surf, (80,80,100), (40,90,40,58))
        pygame.image.save(surf, castle_path)
        print("Placeholder castle created.")
    except Exception as e:
        print("Failed to create castle placeholder:", e)

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except Exception as e:
    print("Warning: audio mixer init failed:", e)
    SOUND_ENABLED = False

def load_sfx(folder, filename):
    path = os.path.join(ASSETS_DIR, folder, "sfx", filename)
    if SOUND_ENABLED and os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print("Failed to load SFX:", path, e)
    return None

sfx_sword_swipe    = load_sfx("knight", "sword_swipe.wav")
sfx_sword_hit      = load_sfx("knight", "sword_hit.wav")
sfx_level_complete = load_sfx("knight", "level_complete.wav")

sfx_laser          = load_sfx("space", "laser.wav")
sfx_explosion      = load_sfx("space", "explosion.wav")
sfx_ship_hit       = load_sfx("space", "ship_hit.wav")

def slice_sheet(path, frame_w, frame_h):
    if not os.path.exists(path): return []
    img = pygame.image.load(path).convert_alpha()
    w,h = img.get_width(), img.get_height()
    cols = max(1, w // frame_w); rows = max(1, h // frame_h)
    frames=[]
    for ry in range(rows):
        for cx in range(cols):
            x,y = cx*frame_w, ry*frame_h
            if x+frame_w<=w and y+frame_h<=h:
                frames.append(img.subsurface(pygame.Rect(x,y,frame_w,frame_h)).copy())
    return frames

def normalize_and_scale(frames, scale=2, pad_to=None):
    if not frames: return [], []
    if pad_to is None:
        max_w = max(f.get_width() for f in frames)
        max_h = max(f.get_height() for f in frames)
    else:
        max_w, max_h = pad_to
    out=[]
    for f in frames:
        surf = pygame.Surface((max_w,max_h), pygame.SRCALPHA)
        x=(max_w-f.get_width())//2; y=max_h-f.get_height()
        surf.blit(f,(x,y))
        sw,sh = int(max_w*scale), int(max_h*scale)
        out.append(pygame.transform.scale(surf,(sw,sh)).convert_alpha())
    flipped=[pygame.transform.flip(f,True,False) for f in out]
    return out, flipped

class PlayerKnight(pygame.sprite.Sprite):
    def __init__(self, x, y, idle, idle_f, walk, walk_f, jump, jump_f, attack, attack_f):
        super().__init__()
        self.idle, self.idle_f = idle, idle_f
        self.walk, self.walk_f = walk, walk_f
        self.jump, self.jump_f = jump, jump_f
        self.attack, self.attack_f = attack, attack_f
        self.image = self.idle[0] if self.idle else pygame.Surface((64,64))
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.vel_y=0; self.on_ground=True; self.facing_right=True
        self.attacking=False; self.attack_timer=0
        self.anim_idx=0; self.anim_t=0; self.current=None
        self.health=5; self.hit_cool=0
    def update(self, keys, dt):
        dx=0; moving=False
        if keys[pygame.K_LEFT]: dx=-5; moving=True; self.facing_right=False
        if keys[pygame.K_RIGHT]: dx=5; moving=True; self.facing_right=True
        if keys[pygame.K_SPACE] and self.on_ground: self.vel_y=-16; self.on_ground=False
        if keys[pygame.K_a] and self.attack_timer<=0:
            self.attacking=True; self.attack_timer=12
            if SOUND_ENABLED and sfx_sword_swipe:
                try: sfx_sword_swipe.play()
                except: pass
        if self.attack_timer>0: self.attack_timer-=1
        else: self.attacking=False
        self.vel_y += 1
        self.rect.y += self.vel_y
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y; self.vel_y=0; self.on_ground=True
        self.rect.x += dx
        if self.attacking:
            frames = self.attack if self.facing_right else self.attack_f; speed=80
        elif not self.on_ground:
            frames = self.jump if self.facing_right else self.jump_f; speed=100
        elif moving:
            frames = self.walk if self.facing_right else self.walk_f; speed=60
        else:
            frames = self.idle if self.facing_right else self.idle_f; speed=140
        if self.current is not frames:
            self.current = frames; self.anim_idx=0; self.anim_t=0
        if frames:
            self.anim_t += dt
            if self.anim_t >= speed:
                self.anim_t = 0; self.anim_idx = (self.anim_idx+1) % len(frames)
            mid = self.rect.midbottom
            self.image = frames[self.anim_idx]
            self.rect = self.image.get_rect(); self.rect.midbottom = mid
        if self.hit_cool>0: self.hit_cool-=1

class EnemyKnight(pygame.sprite.Sprite):
    def __init__(self, x, y, frames, frames_f, speed=2, hp=1):
        super().__init__()
        self.frames, self.frames_f = frames, frames_f
        self.idx=0; self.anim_t=0; self.current=frames
        self.image = frames[0] if frames else pygame.Surface((48,48))
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.speed = speed; self.hp = hp; self.invul=0
    def update(self, dt):
        self.rect.x += self.speed
        if self.rect.left < 100 or self.rect.right > WIDTH - 140: self.speed *= -1
        frames = self.frames_f if self.speed<0 and self.frames_f else self.frames
        if self.current is not frames:
            self.current = frames; self.idx=0; self.anim_t=0
        self.anim_t += dt
        if self.anim_t > 80:
            self.anim_t=0; self.idx = (self.idx+1) % (len(frames) or 1)
        if frames:
            mid = self.rect.midbottom
            self.image = frames[self.idx]
            self.rect = self.image.get_rect(); self.rect.midbottom = mid
        if self.invul>0: self.invul -= 1
    def hit(self):
        if self.invul>0: return
        self.hp -= 1; self.invul=10
        if self.hp<=0: self.kill()

class KnightLevel:
    def __init__(self, name, bg_files, decor_list, enemy_specs):
        self.name=name; self.bg_files=bg_files; self.decor_list=decor_list; self.enemy_specs=enemy_specs
    def load_bg(self):
        for fn in self.bg_files:
            if os.path.exists(asset_path("knight", fn)):
                return load_image("knight", fn, (WIDTH, HEIGHT))
        return None

class KnightGame:
    def __init__(self, story):
        self.story = story.lower()
        idle_frames, idle_f = normalize_and_scale(slice_sheet(asset_path("knight","knight_idle.png"),100,80), scale=2, pad_to=(100,80))
        walk_frames, walk_f = normalize_and_scale(slice_sheet(asset_path("knight","knight_walk.png"),100,80), scale=2, pad_to=(100,80))
        jump_frames, jump_f = normalize_and_scale(slice_sheet(asset_path("knight","knight_jump.png"),30,80), scale=3, pad_to=(30,80))
        attack_frames, attack_f = normalize_and_scale(slice_sheet(asset_path("knight","knight_attack.png"),40,80), scale=3, pad_to=(40,80))
        if not idle_frames: idle_frames=[load_image("knight","knight_idle.png",(100,80))]
        if not walk_frames: walk_frames=[load_image("knight","knight_walk.png",(100,80))]
        if not jump_frames: jump_frames=[load_image("knight","knight_jump.png",(30,80))]
        if not attack_frames: attack_frames=[load_image("knight","knight_attack.png",(40,80))]
        idle_f = [pygame.transform.flip(f,True,False) for f in idle_frames]
        walk_f = [pygame.transform.flip(f,True,False) for f in walk_frames]
        jump_f = [pygame.transform.flip(f,True,False) for f in jump_frames]
        attack_f = [pygame.transform.flip(f,True,False) for f in attack_frames]
        self.player = PlayerKnight(120, GROUND_Y, idle_frames, idle_f, walk_frames, walk_f, jump_frames, jump_f, attack_frames, attack_f)
        self.player_group = pygame.sprite.Group(self.player)
        forest = KnightLevel("Forest", ["sky.png","pine.png","mountains.png"], ["tree.png","rock.png","bush.png"], [("snake",3),("hyena",1)])
        desert = KnightLevel("Desert", ["desert_bg.png"], ["cactus.png","ruins.png"], [("hyena",3)])
        grave = KnightLevel("Graveyard", ["graveyard_bg.png"], ["tombstone.png","dead_tree.png"], [("mummy",2)])
        chosen=[]
        if any(k in self.story for k in ["forest","woods","tree"]): chosen.append(forest)
        if any(k in self.story for k in ["desert","sand","dune"]): chosen.append(desert)
        if any(k in self.story for k in ["tomb","grave","mummy","crypt","graveyard"]): chosen.append(grave)
        if not chosen: chosen=[forest, desert, grave]
        self.levels = chosen
        s_frames, s_frames_f = normalize_and_scale(slice_sheet(asset_path("knight","snake_walk.png"),16,48), scale=3)
        h_frames, h_frames_f = normalize_and_scale(slice_sheet(asset_path("knight","hyena_walk.png"),24,48), scale=3)
        m_frames, m_frames_f = normalize_and_scale(slice_sheet(asset_path("knight","mummy_walk.png"),24,48), scale=3)
        self.enemy_frames = {
            "snake": (s_frames or [load_image("knight","snake_walk.png",(32,48))], s_frames_f or []),
            "hyena": (h_frames or [load_image("knight","hyena_walk.png",(48,48))], h_frames_f or []),
            "mummy": (m_frames or [load_image("knight","mummy_walk.png",(48,48))], m_frames_f or [])
        }
        self.current_index=0; self.enemy_group = pygame.sprite.Group(); self.debug=False
        self.spawn_current_level()

    def spawn_current_level(self):
        self.enemy_group.empty()
        lvl = self.levels[self.current_index]
        x = 360
        for typ,count in lvl.enemy_specs:
            frames, frames_f = self.enemy_frames.get(typ, ([load_image("knight",f"{typ}_walk.png")], []))
            for i in range(count):
                speed = 2 if typ=="snake" else (3 if typ=="hyena" else 1)
                hp = 1 if typ!="mummy" else 3
                e = EnemyKnight(x + i*60, GROUND_Y, frames, frames_f, speed=speed, hp=hp)
                self.enemy_group.add(e)
            x += 220
        print(f"Spawned level '{self.levels[self.current_index].name}' -> enemies: {len(self.enemy_group)}")

    def draw_background_and_ground(self, lvl):
        bg = lvl.load_bg()
        if bg:
            screen.blit(pygame.transform.scale(bg,(WIDTH,HEIGHT)), (0,0))
        else:
            if lvl.name.lower().startswith("desert"):
                screen.fill((245, 222, 179))
            elif lvl.name.lower().startswith("grave"):
                screen.fill((45,45,60))
            else:
                screen.fill((120,180,240))
        top_tile = None
        for name in ["grass.png", "sand_tile.png", "spooky_ground.png"]:
            if os.path.exists(asset_path("knight", name)):
                top_tile = load_image("knight", name, (64,64)); break
        if top_tile is None:
            top_tile = pygame.Surface((64,64)); top_tile.fill((34,139,34))
        under_tile = None
        for name in ["ground.png", "sand_tile.png", "spooky_ground.png"]:
            if os.path.exists(asset_path("knight", name)):
                under_tile = load_image("knight", name, (64,64)); break
        if under_tile is None:
            under_tile = pygame.Surface((64,64)); under_tile.fill((139,69,19))
        tile = pygame.transform.scale(top_tile,(64,64)); g = pygame.transform.scale(under_tile,(64,64))
        for x in range(0, WIDTH, 64):
            screen.blit(tile,(x,GROUND_Y))
            screen.blit(g,(x,GROUND_Y+64))
        castle = load_image("knight","castle.png",(120,160))
        screen.blit(pygame.transform.scale(castle,(120,160)), (WIDTH-140, GROUND_Y-160))

    def run(self):
        while self.current_index < len(self.levels):
            lvl = self.levels[self.current_index]
            level_complete=False
            while not level_complete:
                dt = clock.tick(FPS)
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if ev.type == pygame.KEYDOWN and ev.key==pygame.K_d:
                        self.debug = not self.debug
                keys = pygame.key.get_pressed()
                self.player_group.update(keys, dt)
                self.enemy_group.update(dt)
                for e in list(self.enemy_group):
                    if self.player.rect.colliderect(e.rect):
                        if self.player.attacking:
                            e.hit()
                            if SOUND_ENABLED and sfx_sword_hit:
                                try: sfx_sword_hit.play()
                                except: pass
                        else:
                            if self.player.hit_cool<=0:
                                self.player.health -= 1; self.player.hit_cool=40
                                if self.player.health<=0:
                                    print("Player died. Game Over.")
                                    return False
                if self.player.rect.right >= WIDTH - 120 or len(self.enemy_group)==0:
                    if SOUND_ENABLED and sfx_level_complete:
                        try: sfx_level_complete.play()
                        except: pass
                    print(f"Level '{lvl.name}' complete!")
                    level_complete=True
                self.draw_background_and_ground(lvl)
                self.enemy_group.draw(screen)
                self.player_group.draw(screen)
                if self.debug:
                    pygame.draw.rect(screen,(255,0,0), self.player.rect,2)
                    for e in self.enemy_group:
                        pygame.draw.rect(screen,(255,255,0), e.rect,2)
                hud = FONT.render(f"{lvl.name}  HP:{self.player.health}  Level {self.current_index+1}/{len(self.levels)} (D toggle)", True, (255,255,255))
                screen.blit(hud,(8,8))
                pygame.display.flip()
            self.current_index += 1
            if self.current_index < len(self.levels):
                print("Loading next Knight level...")
                self.player.rect.midbottom = (120, GROUND_Y)
                self.spawn_current_level()
                time.sleep(0.5)
        print("Knight campaign complete!")
        return True

class PlayerShip(pygame.sprite.Sprite):
    def __init__(self, img, x, y, speed=5, hp=5):
        super().__init__()
        self.image=img; self.rect=self.image.get_rect(center=(x,y))
        self.speed=speed; self.hp=hp; self.cool=0
    def update(self, keys):
        dx=dy=0
        if keys[pygame.K_LEFT]: dx-=self.speed
        if keys[pygame.K_RIGHT]: dx+=self.speed
        if keys[pygame.K_UP]: dy-=self.speed
        if keys[pygame.K_DOWN]: dy+=self.speed
        self.rect.x+=dx; self.rect.y+=dy
        self.rect.clamp_ip(pygame.Rect(0,0,WIDTH,HEIGHT))
    def tick(self):
        if self.cool>0: self.cool-=1
    def shoot(self, bullets, bullet_img):
        if self.cool<=0:
            bullets.add(Bullet(bullet_img, self.rect.centerx, self.rect.top-10, -10))
            self.cool=12
            if SOUND_ENABLED and sfx_laser:
                try: sfx_laser.play()
                except: pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, img, x, y, vy):
        super().__init__()
        self.image=img; self.rect=self.image.get_rect(center=(x,y)); self.vy=vy
    def update(self):
        self.rect.y += self.vy
        if self.rect.bottom<0 or self.rect.top>HEIGHT: self.kill()

class SpaceEnemy(pygame.sprite.Sprite):
    def __init__(self, img, x, y, speed=2, hp=1, pattern="straight"):
        super().__init__()
        self.image=img; self.rect=self.image.get_rect(center=(x,y))
        self.speed=speed; self.hp=hp; self.pattern=pattern; self.t=0
    def update(self):
        self.t+=1
        if self.pattern=="zig":
            self.rect.x += int(self.speed * (1 if (self.t//20)%2==0 else -1))
            self.rect.y += max(1, self.speed//2)
        else:
            self.rect.y += self.speed
        if self.rect.top > HEIGHT: self.kill()
    def hit(self):
        self.hp -= 1
        if self.hp <= 0: self.kill()

class SpaceMission:
    def __init__(self, name, waves, bg_list):
        self.name=name; self.waves=waves; self.bg_list=bg_list
    def load_bg(self):
        for fn in self.bg_list:
            if os.path.exists(asset_path("space", fn)):
                return load_image("space", fn, (WIDTH, HEIGHT))
        return None

class SpaceGame:
    def __init__(self, story):
        self.story = story.lower()
        self.bg_default = load_image("space","space_bg.png",(WIDTH,HEIGHT))
        self.player_img = load_image("space","player_ship.png",(48,48))
        self.bullet_img = load_image("space","bullet.png",(6,12))
        self.enemy_imgs = {
            "alien": load_image("space","enemy_alien.png",(32,32)),
            "drone": load_image("space","enemy_drone.png",(36,36)),
            "boss": load_image("space","enemy_boss.png",(96,96))
        }
        self.player = PlayerShip(self.player_img, WIDTH//2, HEIGHT-80, speed=6, hp=5)
        self.player_group = pygame.sprite.Group(self.player)
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        m1 = SpaceMission("Outer Orbit", [{"type":"alien","count":6,"speed":2,"hp":1,"pattern":"straight"}], ["space_bg.png","nebula_bg.png"])
        m2 = SpaceMission("Asteroid Belt", [{"type":"drone","count":5,"speed":3,"hp":2,"pattern":"zig"},{"type":"alien","count":4,"speed":2,"hp":1}], ["asteroid_bg.png","space_bg.png"])
        m3 = SpaceMission("Deep Space", [{"type":"boss","count":1,"speed":1,"hp":10,"pattern":"straight"}], ["nebula_bg.png","space_bg.png"])
        self.missions = [m1, m2, m3]
 
        self.current_idx=0; self.debug=False

    def spawn_wave(self, wave):
        t = wave.get("type","alien"); count=wave.get("count",5)
        for i in range(count):
            x = random.randint(40, WIDTH-40); y = -random.randint(20,300) - i*40
            img = self.enemy_imgs.get(t, self.enemy_imgs["alien"])
            self.enemies.add(SpaceEnemy(img,x,y,speed=wave.get("speed",2),hp=wave.get("hp",1),pattern=wave.get("pattern","straight")))

    def run(self):
        while self.current_idx < len(self.missions):
            mission = self.missions[self.current_idx]
            mission_complete=False
            bg = mission.load_bg() or self.bg_default
            self.enemies.empty(); self.bullets.empty()
            self.player.rect.center = (WIDTH//2, HEIGHT-80)
            wave_idx=0; wave_timer=30
            while not mission_complete:
                dt = clock.tick(FPS)
                events = pygame.event.get()
                for ev in events:
                    if ev.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if ev.type == pygame.KEYDOWN and ev.key==pygame.K_d:
                        self.debug = not self.debug
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    self.player.shoot(self.bullets, self.bullet_img)
                if wave_idx < len(mission.waves):
                    if wave_timer <= 0:
                        self.spawn_wave(mission.waves[wave_idx])
                        wave_timer = 400
                        wave_idx += 1
                    else:
                        wave_timer -= 1
                self.player_group.update(keys)
                self.bullets.update()
                self.enemies.update()
                for b in list(self.bullets):
                    hit = pygame.sprite.spritecollideany(b, self.enemies)
                    if hit:
                        try: hit.hit()
                        except: hit.kill()
                        b.kill()
                        if SOUND_ENABLED and sfx_explosion:
                            try: sfx_explosion.play()
                            except: pass
                if pygame.sprite.spritecollideany(self.player, self.enemies):
                    for e in pygame.sprite.spritecollide(self.player, self.enemies, True):
                        self.player.hp -= 1
                        if SOUND_ENABLED and sfx_ship_hit:
                            try: sfx_ship_hit.play()
                            except: pass
                    if self.player.hp <= 0:
                        print("Player died. Game Over.")
                        return False
                self.player.tick()
                if wave_idx >= len(mission.waves) and len(self.enemies) == 0:
                    mission_complete = True
                screen.blit(pygame.transform.scale(bg,(WIDTH,HEIGHT)),(0,0))
                self.enemies.draw(screen)
                self.bullets.draw(screen)
                self.player_group.draw(screen)
                if self.debug:
                    pygame.draw.rect(screen,(255,0,0), self.player.rect,2)
                hud = FONT.render(f"{mission.name}  HP:{self.player.hp}  Mission {self.current_idx+1}/{len(self.missions)} (D toggle)", True, (255,255,255))
                screen.blit(hud,(8,8))
                pygame.display.flip()
            print(f"Mission '{mission.name}' complete.")
            self.current_idx += 1
            time.sleep(0.4)
        print("All space missions complete!")
        return True

def run_flow():
    global chosen_mode
    if chosen_mode == "knight":
        print("Starting Knight campaign...")
        kg = KnightGame(story)
        kg.run()
    else:
        print("Starting Space campaign...")
        sg = SpaceGame(story)
        sg.run()

if __name__ == "__main__":
    run_flow()
    pygame.quit()
    print("Exited.")
