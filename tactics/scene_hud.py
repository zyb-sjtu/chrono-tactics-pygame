"""Overlay-only UI; hit testing returns intent without touching combat state."""

import pygame

from .actions import UIAction
from .panel import load_fonts


class SceneHUD:
    def __init__(self, viewport_size, margin=24):
        fonts, self.chinese = load_fonts()
        self.title_font, self.font, self.small_font = fonts
        self.card = pygame.Rect(margin,margin,350,254)
        self.history = pygame.Rect(margin+370,margin,490,112)
        x,y = self.card.topleft
        self._buttons = {UIAction.UNDO:pygame.Rect(x+12,y+210,100,32),
                         UIAction.SKIP_PHASE:pygame.Rect(x+122,y+210,104,32),
                         UIAction.END_TURN:pygame.Rect(x+236,y+210,102,32)}
        self._cards = []
        for rect in (self.card,self.history):
            layer = pygame.Surface(rect.size,pygame.SRCALPHA)
            layer.fill((20,26,31,205))
            pygame.draw.rect(layer,(143,139,113,180),layer.get_rect(),1,border_radius=8)
            self._cards.append((rect,layer))

    def contains(self, position):
        """Consume the full HUD surface, including labels and gaps between buttons."""
        return self.card.collidepoint(position) or self.history.collidepoint(position)

    def hit_test(self, position):
        return next((action for action,rect in self._buttons.items() if rect.collidepoint(position)),None)

    def _text(self,surface,value,position,width,font=None,color=(226,226,211)):
        font = self.small_font if font is None else font
        while value and font.size(value)[0] > width:
            value = value[:-1]
        surface.blit(font.render(value,True,color),position)

    def draw(self,surface,view):
        for rect,layer in self._cards:
            surface.blit(layer,rect)
        x,y = self.card.x+14,self.card.y+10
        cn = self.chinese
        actor = view.active
        title = ("第 {} 回合" if cn else "ROUND {}").format(view.round_number)
        self._text(surface,title,(x,y),320,self.title_font,(240,211,148))
        if view.finished:
            winner = {"ally":"蓝方获胜","enemy":"红方获胜","draw":"平局"}.get(view.winner,view.winner)
            state = "战斗结束 · " + winner if cn else "FINISHED / {} wins".format(view.winner)
        else:
            name = actor.name if cn else actor.uid
            phase = {"move":"移动","attack":"攻击","resolving":"结算中"}[view.phase] if cn else view.phase
            state = ("行动：{} [{}] · {}" if cn else "Active: {} [{}] / {}").format(name,actor.uid,phase)
        self._text(surface,state,(x,y+36),320,self.font)
        unit = view.selected
        if unit:
            name = unit.name if cn else unit.uid
            self._text(surface,("查看：{} [{}]" if cn else "Inspect: {} [{}]").format(name,unit.uid),(x,y+68),320,self.font)
            stats = (("生命" if cn else "HP","{}/{}".format(unit.health,unit.max_health)),
                     ("攻击" if cn else "ATK",unit.attack),("防御" if cn else "DEF",unit.defense),
                     ("速度" if cn else "SPD",unit.speed),("移动" if cn else "MOVE",unit.movement),
                     ("范围" if cn else "RANGE",1))
            for index,(label,value) in enumerate(stats):
                self._text(surface,"{}: {}".format(label,value),(x+(index%2)*170,y+100+(index//2)*25),160,self.font)
        hint = "结算中，请稍候" if cn and view.input_locked else "鼠标选择/行动 · F3 网格" if cn else "Click to inspect/act / F3 grid"
        self._text(surface,hint,(x,y+178),320,color=(163,194,183))
        enabled = {UIAction.UNDO:view.can_undo,UIAction.SKIP_PHASE:view.can_skip,UIAction.END_TURN:view.can_end_turn}
        labels = {UIAction.UNDO:"回溯 [退格]" if cn else "Undo [Bksp]",
                  UIAction.SKIP_PHASE:"跳过 [空格]" if cn else "Skip [Space]",
                  UIAction.END_TURN:"结束 [回车]" if cn else "End [Enter]"}
        for action,rect in self._buttons.items():
            pygame.draw.rect(surface,(65,77,75) if enabled[action] else (40,44,45),rect,border_radius=4)
            label = self.small_font.render(labels[action],True,(241,224,188) if enabled[action] else (110,117,116))
            surface.blit(label,label.get_rect(center=rect.center))
        hx,hy = self.history.x+12,self.history.y+10
        order = " → ".join("{}({})".format(u.uid,u.speed) for u in view.order)
        self._text(surface,("顺序：" if cn else "Order: ")+order,(hx,hy),466,color=(233,202,144))
        for index,message in enumerate(view.log[-3:]):
            self._text(surface,message[0 if cn else 1],(hx,hy+27+index*22),466)
