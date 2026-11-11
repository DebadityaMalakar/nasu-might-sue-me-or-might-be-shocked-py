# Prototype reconstruction of the base game's scripted logo.
define config.name = "Fate Community Port"
define config.screen_width = 800
define config.screen_height = 600
define config.has_sound = True
define config.quit_action = Quit(confirm=False)

transform logo_c_motion:
    pos (293, 200) alpha 0.0
    easeout 2.5 pos (293, 350) alpha 1.0

transform logo_b_motion:
    pos (340, 336) alpha 0.0
    pause 1.0
    easeout 1.5 pos (395, 336) alpha 1.0
    linear 0.2 pos (404, 289)

transform logo_a_motion:
    pos (310, 185) alpha 0.0
    pause 2.5
    linear 0.2 pos (299, 219) alpha 1.0

init -100 python:
    import sys, json, os
    from pathlib import Path
    sys.path.insert(0, os.path.abspath(os.path.join(config.gamedir, "..", "..")))
    import startup
    import route_selection
    try:
        startup_config = json.loads(startup.CONFIG_PATH.read_text(encoding="utf-8"))
        startup_base = Path(startup_config["games"][startup_config["selected"]])
        startup.prepare(startup_base, Path(config.gamedir) / "generated", Path(startup_config["patches"]))
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
    scene expression "generated/rogo_fixb3.png" with Dissolve(0.4)
    show expression "generated/rogo_fix0.png" as logo_mask with Dissolve(0.2)
    # The original uses a custom spline and mask here; this is an approximation.
    $ renpy.pause(2.5, hard=False)
    scene expression "generated/rogo_fix.png" with Dissolve(0.8)
    $ renpy.pause(3.0, hard=False)
    scene expression Solid("#fff") with Dissolve(0.8)
    stop sound fadeout 0.2
    return

screen main_menu():
    tag menu
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
    def opening_page_cues(page):
        if page == 0:
            renpy.music.play("generated/opening_bgm43.ogg", channel="music", loop=True)
        elif page == 8:
            renpy.music.stop(channel="music", fadeout=3.0)
        elif page == 10:
            renpy.music.play("generated/opening_bgm42.ogg", channel="music", loop=True)
        elif page == 27:
            renpy.music.stop(channel="music", fadeout=2.0)
        elif page == 34:
            renpy.music.play("generated/opening_se019.wav", channel="sound")
        elif page == 36:
            renpy.music.play("generated/opening_bgm03.ogg", channel="music", loop=True, fadein=1.0)
        elif page == 64:
            renpy.music.play("generated/opening_se247.wav", channel="sound")
        elif page == 71:
            renpy.music.stop(channel="music", fadeout=3.0)
        if page in (5, 8, 10, 11, 12, 15, 16, 19, 25, 27, 34, 35, 36, 49):
            renpy.transition(Dissolve(0.6))

label start:
    scene black
    $ preview_file = Path(config.gamedir) / "generated" / "opening_preview.json"
    $ preview_pages = json.loads(preview_file.read_text(encoding="utf-8"))
    $ cue_file = Path(config.gamedir) / "generated" / "opening_voice_cues.json"
    $ preview_voice_cues = json.loads(cue_file.read_text(encoding="utf-8"))
    $ jump_value = os.environ.pop("FATE_PORT_JUMP_PAGE", "1")
    $ jump_index = int(jump_value) - 1 if jump_value.isdecimal() else 0
    $ jump_index = jump_index if 0 <= jump_index < len(preview_pages) else 0
    if jump_index <= 7:
        $ opening_page_cues(0)
    elif 10 <= jump_index <= 26:
        $ opening_page_cues(10)
    elif 36 <= jump_index <= 70:
        $ opening_page_cues(36)
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
    if page_index <= 4:
        add Transform("generated/opening_fire.webp", xysize=(800, 600))
    elif page_index <= 7:
        add Transform("generated/opening_aftermath.webp", xysize=(800, 600))
    elif page_index == 10 or 25 <= page_index <= 35:
        add Solid("#000")
    elif page_index <= 11:
        add Solid("#fff")
    elif page_index == 15:
        add Transform("generated/opening_sky.webp", xysize=(800, 600))
    elif 36 <= page_index <= 48:
        add Transform("generated/opening_shed.webp", xysize=(800, 600))
    elif page_index >= 49:
        add Transform("generated/opening_shed_inner.webp", xysize=(800, 600))
    else:
        add Transform("generated/opening_hospital.webp", xysize=(800, 600))
    if page_index == 49:
        add Transform("generated/opening_sakura_13a.webp", xysize=(260, 545)) xalign 0.5 yalign 1.0
    elif page_index == 50:
        add Transform("generated/opening_sakura_13b.webp", xysize=(260, 545)) xalign 0.5 yalign 1.0
    elif page_index == 51:
        add Transform("generated/opening_sakura_06a.webp", xysize=(260, 545)) xalign 0.5 yalign 1.0
    elif page_index == 52:
        add Transform("generated/opening_sakura_09a.webp", xysize=(260, 545)) xalign 0.5 yalign 1.0
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
    frame:
        xalign 0.5 yalign 0.5 padding (24, 24)
        vbox:
            spacing 12
            for caption, requirements, result in choices:
                textbutton caption:
                    sensitive route_selection.choice_available(frozenset(requirements), frozenset(loaded_games))
                    action Return(result)
                    text_insensitive_color "#777777"
