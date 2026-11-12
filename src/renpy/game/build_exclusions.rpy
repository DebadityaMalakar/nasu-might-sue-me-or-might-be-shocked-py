# Original game content is generated locally and must not enter distributions.
init python:
    build.classify("game/generated/**", None)
    build.classify("game/episodes/episode_1_source.json", None)
    build.classify("game/episodes/episode_2.json", None)
