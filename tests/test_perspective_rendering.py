"""Public-input acceptance for projected combat, UI, resources and real CLI."""

from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.assets import Sprite
from tactics.content import load_content
from tactics.data_files import DataError
from tactics.game import Game
from tactics.presentation_layout import load_presentation

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = "presentations/war_torn_8x8.json"


def combat_trace(check, game, capture=None):
    trace = []

    def observe(name):
        game.draw()
        trace.append(game.controller.get_view_state())
        if capture: capture(name,game)
        return trace[-1]

    def click(cell):
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=game.geometry.cell_center(cell)))

    def key(value):
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=value))

    initial = observe('initial')
    # Inspection and reselection use reverse picking, including near/far cells.
    for uid in ('D2','A1','A2'):
        unit = next(u for u in initial.units if u.uid==uid)
        click(unit.cell)
        check.assertEqual(game.controller.get_view_state().selected.uid,uid)
    token = None
    for index,(move,target) in enumerate((((4,3),(5,3)),((5,2),(6,2)),((6,4),(6,5)))):
        click(move)
        check.assertEqual(observe('move'+str(index)).active.cell,move)
        click(target)
        resolving = observe('attack'+str(index))
        check.assertEqual(resolving.phase,'resolving')
        if token is None: token = resolving.pending_resolution
        for value in (pygame.K_BACKSPACE,pygame.K_RETURN,pygame.K_SPACE): key(value)
        check.assertEqual(game.controller.get_view_state(),resolving)
        game.update(.2)
        observe('death'+str(index))
        game.update(1)
        state = observe('handoff'+str(index))
        check.assertFalse(game.effects.busy)
        if index < 2:
            while state.active.uid!='A2':
                key(pygame.K_RETURN)
                state=observe('skip')
            check.assertEqual(state.round_number,index+2)
    check.assertEqual((state.phase,state.winner),('finished','ally'))
    observe('finished')
    while game.controller.get_view_state().can_undo:
        key(pygame.K_BACKSPACE)
        observe('undo')
    restored = observe('revived')
    check.assertEqual(restored.units,initial.units)
    check.assertEqual(restored.board,initial.board)
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(),restored)
    return tuple(trace)


class PerspectiveRenderingChecks(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_calibration_picker_undo_preview_and_save_raw_draft(self):
        from scripts.calibrate_board import DEFAULT, load_observations, pick
        data,geometry=load_observations(DEFAULT)
        points=list(data['corners'].values())+[s['image'] for s in data['samples']]
        events=[]
        # Mark then undo a duplicate corner; saved points must be actual clicks only.
        for index,point in enumerate(points):
            position=geometry.fit.to_screen(point)
            click=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=position)
            events.append(click)
            if index==1:
                events.extend((pygame.event.Event(pygame.KEYDOWN,key=pygame.K_BACKSPACE),click))
        events.extend(pygame.event.Event(pygame.KEYDOWN,key=key) for key in (pygame.K_p,pygame.K_s))
        events.append(pygame.event.Event(pygame.QUIT))
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'draft.json'
            with patch('pygame.event.get',return_value=events):
                pick(ROOT/data['image'],2,6,output)
            saved=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(saved['status'],'draft')
            self.assertEqual(list(saved['corners'].values()),points[:4])
            self.assertEqual([s['image'] for s in saved['samples']],points[4:])
            self.assertFalse(pygame.display.get_init())

    def test_same_full_combat_trace_as_rectangular_mode(self):
        original=load_content(scenario_file='scenarios/war_torn.json').scenario
        scenario=replace(original,units=tuple(replace(u,health=5) if u.team=='enemy' else u for u in original.units))
        rectangle=Game(scenario,geometric=True)
        expected=combat_trace(self,rectangle)
        pygame.quit()
        perspective=Game(scenario,presentation_file=PRESENTATION)
        actual=combat_trace(self,perspective)
        self.assertEqual(actual,expected)

    def test_hud_consumes_cards_and_buttons_use_controller_actions(self):
        game=Game(presentation_file=PRESENTATION)
        initial=game.controller.get_view_state()
        for unit in initial.units:
            rect=pygame.Rect(game.geometry.body_rect(unit.cell))
            self.assertEqual(game.geometry.cell_at(rect.center),unit.cell)
        for position in ((30,30),(40,180),(410,60)):
            self.assertTrue(game.panel.contains(position))
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=position))
            self.assertEqual(game.controller.get_view_state(),initial)
        skip=(200,250)
        self.assertIs(game.panel.hit_test(skip),UIAction.SKIP_PHASE)
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=skip))
        self.assertEqual(game.controller.get_view_state().phase,'attack')
        self.assertTrue(game.controller.handle_action(UIAction.END_TURN))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(65,250)))
        self.assertEqual(game.controller.get_view_state().units,initial.units)
        self.assertEqual(game.controller.get_view_state().active,initial.active)

    def test_background_and_debug_are_cached_and_translucent(self):
        game=Game(presentation_file=PRESENTATION,debug_grid=True)
        before=game.controller.get_view_state()
        with patch('pygame.image.load',side_effect=AssertionError('frame disk IO')), \
             patch('pygame.transform.smoothscale',side_effect=AssertionError('frame scaling')):
            for _ in range(3):
                game.update(.02)
                game.draw()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3))
            game.draw()
        self.assertFalse(any(game.renderer.debug.values()))
        self.assertEqual(game.controller.get_view_state(),before)
        # Uncovered sky is the original contain-fitted background, not repeated floor tiles.
        expected=pygame.Surface(game.screen.get_size())
        expected.fill((21,30,42))
        game.renderer.background.blit(expected,game.geometry.fit.offset)
        self.assertEqual(game.screen.get_at((1100,140)),expected.get_at((1100,140)))
        center=tuple(round(v) for v in game.geometry.cell_center((2,4)))
        pixel=game.screen.get_at(center)
        self.assertNotEqual(pixel[:3],(76,139,137))  # Range fill preserves image texture via alpha.

    def test_missing_corrupt_and_wrong_sized_background_fail_cleanly(self):
        layout=load_presentation(PRESENTATION)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'backgrounds').mkdir()
            shutil.copyfile(ROOT/'assets/skins/war_torn/manifest.json',root/'manifest.json')
            for kind in ('missing','corrupt','size'):
                with self.subTest(kind=kind):
                    image=root/'backgrounds/battlefield.png'
                    if kind=='corrupt': image.write_bytes(b'not a PNG')
                    elif kind=='size': pygame.image.save(pygame.Surface((20,20)),str(image))
                    with patch('tactics.game.load_presentation',return_value=replace(layout,asset_root=root)):
                        with self.assertRaisesRegex(DataError,'background|battlefield'):
                            Game(presentation_file=PRESENTATION)
                    self.assertFalse(pygame.display.get_init())

    def test_existing_sprite_clips_depth_order_and_no_frame_rescaling(self):
        layout=load_presentation(PRESENTATION)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'skin'
            shutil.copytree(ROOT/'assets/skins/dusk',root)
            (root/'backgrounds').mkdir()
            shutil.copyfile(ROOT/'assets/skins/war_torn/backgrounds/battlefield.png',root/'backgrounds/battlefield.png')
            data=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
            data['images']['battlefield']={'path':'backgrounds/battlefield.png','display_size':[1672,941],'pivot':[0,0],'optional':False}
            data['board']['background']='battlefield'
            (root/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
            with patch('tactics.game.load_presentation',return_value=replace(layout,asset_root=root)):
                game=Game(presentation_file=PRESENTATION)
            calls=[]
            original=Sprite.blit
            def record(sprite,target,anchor):
                if sprite is not game.renderer.background: calls.append(anchor)
                return original(sprite,target,anchor)
            with patch.object(Sprite,'blit',record), \
                 patch('pygame.image.load',side_effect=AssertionError('frame disk IO')), \
                 patch('pygame.transform.smoothscale',side_effect=AssertionError('frame scaling')):
                game.draw()
                self.assertEqual([p[1] for p in calls],sorted(p[1] for p in calls))
                self.assertTrue(game.controller.move_to((4,3)))
                self.assertTrue(game.controller.attack('D1'))
                self.assertTrue(game.effects.body_views())
                self.assertFalse(game.effects.deaths)  # The target uses the cached PNG death clip.
                game.update(.2)
                game.draw()
                game.update(1)
                self.assertTrue(game.controller.undo())
                self.assertFalse(game.effects.body_views())
                game.draw()

    def test_mixed_flags_dimensions_and_font_fallback(self):
        for kwargs in ({'geometric':True},{'scenario_file':'scenarios/training_ground.json'},
                       {'asset_root':ROOT/'assets'},{'content_root':ROOT/'content'}):
            with self.subTest(kwargs=kwargs),self.assertRaisesRegex(DataError,'cannot be combined'):
                Game(presentation_file=PRESENTATION,**kwargs)
        with self.assertRaisesRegex(DataError,'needs --presentation'): Game(debug_grid=True)
        with self.assertRaisesRegex(DataError,'dimensions'):
            Game(load_content(scenario_file='scenarios/river_crossing.json').scenario,presentation_file=PRESENTATION)
        with patch('tactics.panel.Path.is_file',return_value=False), \
             patch('tactics.panel.pygame.font.match_font',side_effect=TypeError('bad registry')):
            game=Game(presentation_file=PRESENTATION)
        self.assertFalse(game.panel.chinese)
        self.assertTrue(game.controller.move_to((4,3)))
        self.assertTrue(game.controller.attack('D1'))
        game.draw()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
        self.assertFalse(pygame.display.get_init())

    def test_real_cli_and_relative_presentation_from_foreign_cwd(self):
        script="""
import runpy,sys,pygame
from tactics.game import Game
original=Game.run
def run(self):
    assert self.screen.get_size()==(1280,720)
    assert all(self.renderer.debug.values())
    self.draw()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    original(self)
    assert not pygame.display.get_init()
    print('PERSPECTIVE_CLI_QUIT_OK')
Game.run=run
sys.argv=[sys.argv[1], '--presentation','presentations/war_torn_8x8.json','--debug-grid']
runpy.run_path(sys.argv[0],run_name='__main__')
"""
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYGAME_HIDE_SUPPORT_PROMPT='1')
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'-c',script,str(ROOT/'main.py')],env=env,cwd=folder,
                                  text=True,capture_output=True,timeout=45)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PERSPECTIVE_CLI_QUIT_OK',result.stdout)
