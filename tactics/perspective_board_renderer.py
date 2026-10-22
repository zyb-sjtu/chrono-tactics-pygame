"""Full background, translucent projected ranges and screen-depth body sorting."""

import pygame


class PerspectiveBoardRenderer:
    def __init__(self, geometry, assets, debug=()):
        self.geometry = geometry
        self.assets = assets
        self.elapsed = 0
        self.debug = dict(debug)
        self.background = assets.background(geometry.reference_size, geometry.fit.scale)
        assets.preload_units(geometry.scales)
        self.label_font = pygame.font.Font(None, 19)
        self.debug_font = pygame.font.Font(None, 16)
        self._debug_layer = self._build_debug_layer()
        self._range_layer = pygame.Surface(tuple(map(int, geometry.viewport_size)), pygame.SRCALPHA)

    def _build_debug_layer(self):
        layer = pygame.Surface(tuple(map(int, self.geometry.viewport_size)), pygame.SRCALPHA)
        for row in range(self.geometry.rows):
            for col in range(self.geometry.cols):
                cell = (col,row)
                polygon = self.geometry.cell_polygon(cell)
                center = self.geometry.cell_center(cell)
                if self.debug.get("show_grid"):
                    pygame.draw.polygon(layer,(130,210,236,180),polygon,1)
                if self.debug.get("show_cell_centers"):
                    pygame.draw.circle(layer,(255,210,90),center,2)
                if self.debug.get("show_coordinates"):
                    label = self.debug_font.render("{},{}".format(col,row),True,(255,248,199))
                    layer.blit(label,label.get_rect(center=center))
        if self.debug.get("show_grid"):
            for name, point in zip(("p00","p10","p11","p01"),self.geometry.corners):
                screen = self.geometry.fit.to_screen(point)
                pygame.draw.circle(layer,(255,160,100),screen,5)
                label = self.debug_font.render(name,True,(255,238,200))
                layer.blit(label,(screen[0]+6,screen[1]-18))
        return layer

    def update(self, elapsed):
        self.elapsed += max(0,elapsed)

    def toggle_debug(self):
        enabled = not any(self.debug.values())
        self.debug = dict.fromkeys(("show_grid","show_cell_centers","show_coordinates"),enabled)
        self._debug_layer = self._build_debug_layer()

    def draw(self, surface, view, bodies=()):
        if (view.cols,view.rows) != (self.geometry.cols,self.geometry.rows):
            raise ValueError("board view and perspective geometry dimensions do not match")
        self.background.blit(surface,self.geometry.fit.offset)
        surface.blit(self._debug_layer,(0,0))
        layer = self._range_layer
        layer.fill((0,0,0,0))
        for cells, color in ((view.move_cells,(76,139,137,70)),(view.attack_cells,(150,57,59,85))):
            for cell in cells:
                pygame.draw.polygon(layer,color,self.geometry.cell_polygon(cell))
        for cell in view.target_cells:
            pygame.draw.polygon(layer,(255,186,146,225),self.geometry.cell_polygon(cell),2)
        surface.blit(layer,(0,0))

        overrides = {body.uid:body for body in bodies}
        drawables = [(self.geometry.depth_at(c),"obstacle:{}:{}".format(*c),"obstacle",c) for c in view.obstacles]
        drawables += [(self.geometry.depth_at(u.cell),u.uid,"unit",u) for u in view.units if u.uid not in overrides]
        drawables += [(self.geometry.depth_at(b.cell),b.uid,"sprite",b) for b in bodies]
        # Shadows precede all bodies. Cached sprites are never modified in-place.
        for _,_,kind,item in drawables:
            cell = item if kind == "obstacle" else item.cell
            x,y = self.geometry.cell_anchor(cell)
            scale = self.geometry.cell_scale(cell)
            pygame.draw.ellipse(surface,(42,33,29),(x-23*scale,y-6*scale,46*scale,11*scale))
        for _,_,kind,item in sorted(drawables,key=lambda entry:entry[:2]):
            cell = item if kind == "obstacle" else item.cell
            anchor = self.geometry.cell_anchor(cell)
            scale = self.geometry.cell_scale(cell)
            rect = pygame.Rect(self.geometry.body_rect(cell))
            if kind == "sprite":
                item.sprite.blit(surface,anchor)
                continue
            if kind == "obstacle":
                sprite = self.assets.board_image("obstacle",scale)
                if sprite:
                    sprite.blit(surface,anchor)
                else:
                    rock = rect.inflate(-rect.width*.3,-rect.height*.3)
                    pygame.draw.rect(surface,(92,89,84),rock,border_radius=6)
                    pygame.draw.line(surface,(172,159,133),rock.topleft,rock.bottomright,2)
                continue
            clip = self.assets.visual(item.definition_id,"idle",scale)
            if clip:
                clip.frame_at(self.elapsed).blit(surface,anchor)
            elif item.team == "ally":
                pygame.draw.circle(surface,(61,131,177),rect.center,round(19*scale))
                pygame.draw.circle(surface,(163,215,227),rect.center,round(19*scale),2)
            else:
                block = rect.inflate(-rect.width*.4,-rect.height*.4)
                pygame.draw.rect(surface,(170,72,64),block,border_radius=3)
                pygame.draw.rect(surface,(235,162,128),block,2,border_radius=3)
        # Every mark and health bar remains above all large neighboring bodies.
        for unit in view.units:
            rect = pygame.Rect(self.geometry.body_rect(unit.cell))
            if unit.uid == view.active_uid:
                pygame.draw.polygon(surface,(239,204,113),self.geometry.cell_polygon(unit.cell),2)
            if unit.uid == view.selected_uid:
                pygame.draw.ellipse(surface,(235,238,219),rect.inflate(8,8),2)
            label = self.label_font.render(unit.uid,True,(255,249,225))
            surface.blit(label,label.get_rect(center=rect.center))
            bar = pygame.Rect(rect.x+6,rect.bottom-3,max(12,rect.width-12),4)
            pygame.draw.rect(surface,(33,30,28),bar)
            fill = bar.copy()
            fill.width = round(bar.width*min(1,unit.health/max(1,unit.max_health)))
            pygame.draw.rect(surface,(116,192,151),fill)
