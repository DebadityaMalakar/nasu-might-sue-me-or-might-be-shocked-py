# Prototype reconstruction of the base game's scripted logo.
define config.name = "Fate Community Port"
define config.screen_width = 1920
define config.screen_height = 1080
define config.has_sound = True
define config.quit_action = Quit(confirm=False)

transform stage_4_3:
    zoom 1.8
    xalign 0.5 yalign 0.5

transform logo_c_motion:
    zoom 1.8
    pos (767, 360) alpha 0.0
    easeout 2.5 pos (767, 630) alpha 1.0

transform logo_b_motion:
    zoom 1.8
    pos (852, 605) alpha 0.0
    pause 1.0
    easeout 1.5 pos (951, 605) alpha 1.0
    linear 0.2 pos (967.2, 520)

transform logo_a_motion:
    zoom 1.8
    pos (798, 333) alpha 0.0
    pause 2.5
    linear 0.2 pos (778, 394) alpha 1.0

init -100 python:
    import sys, json, os
    from pathlib import Path
    sys.path.insert(0, os.path.abspath(os.path.join(config.gamedir, "..", "..")))
    import startup
    import route_selection
    from episode_manifest import load_manifest
    try:
        startup_config = json.loads(startup.CONFIG_PATH.read_text(encoding="utf-8"))
        startup_base = Path(startup_config["games"][startup_config["selected"]])
        startup.prepare(startup_base, Path(config.gamedir) / "generated", Path(startup_config["patches"]))
        opening_manifest = load_manifest(Path(config.gamedir) / "episodes" / "episode_1.json", startup.PREVIEW_PAGE_COUNT)
    except Exception as error:
        raise RuntimeError("Startup archive verification failed: {}".format(error))

label splashscreen:
    if os.environ.get("FATE_PORT_JUMP_PAGE"):
        call start
    else:
        call startup_logo
    return

label startup_logo:
    scene black
    play sound "generated/typemoon_ci.wav"
    show expression "generated/rogo_c.png" as logo_c at logo_c_motion
    show expression "generated/rogo_bi2.png" as logo_b at logo_b_motion
    show expression "generated/rogo_ai.png" as logo_a at logo_a_motion
    $ renpy.pause(2.7, hard=False)
    scene expression Transform("generated/rogo_fixb3.png", xysize=(1440, 1080), xpos=240) with Dissolve(0.4)
    show expression Transform("generated/rogo_fix0.png", xysize=(1440, 1080), xpos=240) as logo_mask with Dissolve(0.2)
    # The original uses a custom spline and mask here; this is an approximation.
    $ renpy.pause(2.5, hard=False)
    scene expression Transform("generated/rogo_fix.png", xysize=(1440, 1080), xpos=240) with Dissolve(0.8)
    $ renpy.pause(3.0, hard=False)
    scene expression Solid("#fff") with Dissolve(0.8)
    stop sound fadeout 0.2
    return

screen main_menu():
    tag menu
    fixed:
        xysize (800, 600)
        at stage_4_3
        add Solid("#000")
        add Transform("generated/title_circle.webp", xysize=(420, 420), alpha=0.62) xalign 0.5 ypos 12
        add Transform("generated/title_logo.webp", xysize=(330, 310)) xalign 0.5 ypos 16
        add Transform("generated/title_subtext.webp", xysize=(310, 34)) xalign 0.5 ypos 327
        textbutton "LOAD":
            xpos 180 ypos 467 xanchor 0.5
            text_size 22 text_color "#e2f3ff" text_hover_color "#8bc6ff"
            action Notify("Save loading is not implemented yet.")
        textbutton "START":
            xpos 400 ypos 467 xanchor 0.5
            text_size 22 text_color "#e2f3ff" text_hover_color "#8bc6ff"
            action Start()
        textbutton "CONFIG":
            xpos 620 ypos 467 xanchor 0.5
            text_size 22 text_color "#e2f3ff" text_hover_color "#8bc6ff"
            action Show("prototype_config")
        text "© TYPE-MOON / KADOKAWA SHOTEN PUBLISHING CO., LTD.":
            xalign 0.5 ypos 560 size 13 color "#b9d9ff" outlines [(1, "#447ab0", 0, 0)]
        textbutton "Quit":
            xalign 0.97 yalign 0.97 text_size 12 text_color "#8293a4" action Quit(confirm=False)

screen prototype_config():
    modal True
    fixed:
        xysize (800, 600)
        at stage_4_3
        add Solid("#000b")
        frame:
            xalign 0.5 yalign 0.5 padding (25, 25)
            vbox:
                spacing 15
                text "CONFIG" size 28
                text "Sound volume" size 20
                bar value Preference("sound volume") xsize 300
                textbutton "Close" action Hide("prototype_config")

label main_menu_screen:
    call screen main_menu
    jump main_menu_screen

init python:
    def opening_page_cues(page, seek=False):
        frame = opening_manifest["pages"][page]
        if seek:
            if frame["music_state"]:
                renpy.music.play("generated/" + frame["music_state"], channel="music", loop=True)
            else:
                renpy.music.stop(channel="music")
            return
        for event in frame["events"]:
            if event["type"] == "music_play":
                renpy.music.play("generated/" + event["asset"], channel="music", loop=True, fadein=event.get("fadein", 0))
            elif event["type"] == "music_stop":
                renpy.music.stop(channel="music", fadeout=event.get("fadeout", 0))
            elif event["type"] == "sound_play":
                renpy.music.play("generated/" + event["asset"], channel="sound")
        if frame["transition_seconds"]:
            renpy.transition(Dissolve(frame["transition_seconds"]))

label start:
    scene black
    $ preview_file = Path(config.gamedir) / "generated" / "opening_preview.json"
    $ preview_pages = json.loads(preview_file.read_text(encoding="utf-8"))
    $ cue_file = Path(config.gamedir) / "generated" / "opening_voice_cues.json"
    $ preview_voice_cues = json.loads(cue_file.read_text(encoding="utf-8"))
    $ jump_value = os.environ.pop("FATE_PORT_JUMP_PAGE", "1")
    $ jump_index = int(jump_value) - 1 if jump_value.isdecimal() else 0
    $ jump_index = jump_index if 0 <= jump_index < len(preview_pages) else 0
    $ opening_page_cues(jump_index, seek=jump_index != 0)
    call screen opening_preview_screen(preview_pages, preview_voice_cues, jump_index)
    stop music fadeout 1.0
    stop voice
    return

init python:
    def opening_play_voice(cues, page, position):
        for cue in cues[page]:
            if cue["offset"] == position:
                renpy.music.play("generated/voice_" + cue["name"] + ".wav", channel="voice", loop=False)

screen opening_preview_screen(pages, voice_cues, start_index=0):
    modal True
    default page_index = start_index
    default visible_chars = 0
    on "show" action Function(opening_play_voice, voice_cues, page_index, 0)
    fixed:
        xysize (800, 600)
        at stage_4_3
        $ frame = opening_manifest["pages"][page_index]
        if frame["background"].startswith("#"):
            add Solid(frame["background"])
        else:
            add Transform("generated/" + frame["background"], xysize=(800, 600))
        if frame["sprite"]:
            add Transform("generated/" + frame["sprite"], xysize=(260, 545)) xalign 0.5 yalign 1.0
        add Solid("#0009")
        text "SABER / OPENING - TEXT PREVIEW" xpos 48 ypos 32 size 17 color "#91a9c5"
        text "Opening preview - effects and voice timing still in progress" xpos 48 ypos 58 size 14 color "#9299a2"
        text pages[page_index][:visible_chars]:
            xpos 60 ypos 132 xmaximum 680 size 24 color "#f3f2ee" line_spacing 7 substitute False
        text "[page_index + 1] / [len(pages)]" xpos 60 ypos 540 size 15 color "#9299a2"
        if visible_chars < len(pages[page_index]):
            timer 0.03 repeat True action [Function(opening_play_voice, voice_cues, page_index, visible_chars + 1), SetScreenVariable("visible_chars", min(visible_chars + 1, len(pages[page_index])))]
            textbutton "Show text":
                xalign 0.9 yalign 0.92 action [Function(renpy.music.stop, channel="voice"), SetScreenVariable("visible_chars", len(pages[page_index]))]
            key "dismiss" action [Function(renpy.music.stop, channel="voice"), SetScreenVariable("visible_chars", len(pages[page_index]))]
        elif page_index < len(pages) - 1:
            textbutton "Next":
                xalign 0.9 yalign 0.92 action [Function(renpy.music.stop, channel="voice"), Function(opening_page_cues, page_index + 1), Function(opening_play_voice, voice_cues, page_index + 1, 0), SetScreenVariable("page_index", page_index + 1), SetScreenVariable("visible_chars", 0)]
            key "dismiss" action [Function(renpy.music.stop, channel="voice"), Function(opening_page_cues, page_index + 1), Function(opening_play_voice, voice_cues, page_index + 1, 0), SetScreenVariable("page_index", page_index + 1), SetScreenVariable("visible_chars", 0)]
        else:
            textbutton "Return to title":
                xalign 0.9 yalign 0.92 action Return()
            key "dismiss" action Return()

# The story converter must provide verified game identifiers for each option.
# Each choice is (caption, required_games, result). Empty requirements mean common.
screen route_choices(choices, loaded_games):
    modal True
    fixed:
        xysize (800, 600)
        at stage_4_3
        frame:
            xalign 0.5 yalign 0.5 padding (24, 24)
            vbox:
                spacing 12
                for caption, requirements, result in choices:
                    textbutton caption:
                        sensitive route_selection.choice_available(frozenset(requirements), frozenset(loaded_games))
                        action Return(result)
                        text_insensitive_color "#777777"
