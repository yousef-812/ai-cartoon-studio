from copy import deepcopy

from packages.characters.models import CharacterRead, CharacterRole, VisualIdentity, VoiceProfile
from packages.direction.models import DirectionGenerationRequest, EpisodeDirection
from packages.direction.repair import reconcile_constrained_direction
from packages.scripts.models import EpisodeScript


def _characters() -> list[CharacterRead]:
    return [
        CharacterRead(
            series_id="series-demo",
            name="عمر",
            role=CharacterRole.PROTAGONIST,
            age_range="20-25",
            description="شاب هادئ يرتدي نظارة ويحب إصلاح الأدوات.",
            personality_traits=["هادئ", "دقيق"],
            visual_identity=VisualIdentity(reference_prompt="شاب بنظارة وسترة فيروزية"),
            wardrobe={"default": "سترة فيروزية"},
            speaking_style="هادئ ومباشر",
            voice_profile=VoiceProfile(),
        ),
        CharacterRead(
            series_id="series-demo",
            name="نادر",
            role=CharacterRole.SUPPORTING,
            age_range="20-25",
            description="شاب مرح يلاحظ التفاصيل الصغيرة بسرعة.",
            personality_traits=["مرح", "ملاحظ"],
            visual_identity=VisualIdentity(reference_prompt="شاب بسترة برتقالية ومريلة كحلية"),
            wardrobe={"default": "سترة برتقالية ومريلة كحلية"},
            speaking_style="سريع وودود",
            voice_profile=VoiceProfile(),
        ),
    ]


def _script() -> EpisodeScript:
    scenes = []
    dialogue_by_scene = {
        1: [
            {
                "order": 1,
                "speaker": "عمر",
                "text": "انطفأ المصباح فجأة.",
                "emotion": "قلق هادئ",
                "estimated_duration_seconds": 2.0,
            }
        ],
        2: [
            {
                "order": 1,
                "speaker": "نادر",
                "text": "السلك مفصول هنا.",
                "emotion": "انتباه",
                "estimated_duration_seconds": 2.0,
            }
        ],
        3: [],
        4: [
            {
                "order": 1,
                "speaker": "عمر",
                "text": "اشتغل النور.",
                "emotion": "فرح",
                "estimated_duration_seconds": 1.5,
            }
        ],
    }
    for number in range(1, 5):
        scenes.append(
            {
                "number": number,
                "title": f"مشهد {number}",
                "slugline": "INT. الورشة الرئيسية - NIGHT",
                "location": "الورشة الرئيسية",
                "time_of_day": "ليل",
                "characters": ["عمر", "نادر"],
                "objective": "إكمال إصلاح مصباح الطوارئ بأمان.",
                "conflict": "العاصفة تقطع الإضاءة وتزيد التوتر.",
                "start_state": "المصباح لا يعمل والشخصيتان تبحثان عن السبب.",
                "end_state": "يتقدمان خطوة واضحة نحو إصلاح المصباح.",
                "action_lines": ["يفحص عمر ونادر المصباح فوق طاولة العمل."],
                "dialogue": dialogue_by_scene[number],
                "estimated_duration_seconds": 10,
            }
        )
    return EpisodeScript(
        title="مصباح العاصفة",
        language="ar",
        target_duration_seconds=40,
        total_estimated_duration_seconds=40,
        cold_open="يومض نور الورشة ثم ينطفئ بينما تزداد أصوات العاصفة خارج النافذة.",
        scenes=scenes,
        closing_beat="يضيء المصباح الدافئ وجهي عمر ونادر في نهاية هادئة ومبهجة.",
    )


def test_reconcile_constrained_direction_expands_28_seconds_to_exact_ten_shots() -> None:
    payload = {
        "title": "مصباح العاصفة",
        "aspect_ratio": "16:9",
        "total_estimated_duration_seconds": 28.0,
        "scenes": [
            {
                "scene_number": 1,
                "title": "مشهد 1",
                "estimated_duration_seconds": 8.0,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 1,
                        "duration_seconds": 4.0,
                        "shot_size": "wide shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "The workshop and both characters remain readable.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر", "نادر"],
                        "action": "يومض النور ثم ينطفئ.",
                        "emotion": "قلق",
                        "dialogue_line_orders": [1],
                        "visual_prompt": "Stylized cinematic workshop scene with a flickering lamp.",
                        "animation_notes": ["Keep motion simple."],
                        "continuity_requirements": ["Preserve wardrobe."],
                        "transition": "cut",
                    },
                    {
                        "number": 2,
                        "scene_number": 1,
                        "duration_seconds": 4.0,
                        "shot_size": "medium shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "Readable reaction near the workbench.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر"],
                        "action": "ينظر عمر إلى المصباح.",
                        "emotion": "تركيز",
                        "dialogue_line_orders": [],
                        "visual_prompt": "Stylized medium reaction shot beside the workbench.",
                        "animation_notes": ["Minimal head movement."],
                        "continuity_requirements": ["Preserve glasses and jacket."],
                        "transition": "cut",
                    },
                ],
            },
            {
                "scene_number": 2,
                "title": "مشهد 2",
                "estimated_duration_seconds": 8.0,
                "shots": [
                    {
                        "number": 3,
                        "scene_number": 2,
                        "duration_seconds": 4.0,
                        "shot_size": "medium shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "Nader notices the loose wire.",
                        "location": "الورشة الرئيسية",
                        "characters": ["نادر"],
                        "action": "يشير نادر إلى السلك المفصول.",
                        "emotion": "انتباه",
                        "dialogue_line_orders": [1],
                        "visual_prompt": "Stylized readable shot of Nader noticing a loose wire.",
                        "animation_notes": ["Use a simple pointing gesture."],
                        "continuity_requirements": ["Preserve orange hoodie and navy apron."],
                        "transition": "cut",
                    },
                    {
                        "number": 4,
                        "scene_number": 2,
                        "duration_seconds": 4.0,
                        "shot_size": "close-up reaction",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "A clear silent reaction.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر"],
                        "action": "يومئ عمر موافقًا.",
                        "emotion": "فهم",
                        "dialogue_line_orders": [],
                        "visual_prompt": "Stylized close reaction with stable lighting.",
                        "animation_notes": ["Minimal facial animation."],
                        "continuity_requirements": ["Preserve wardrobe."],
                        "transition": "cut",
                    },
                ],
            },
            {
                "scene_number": 3,
                "title": "مشهد 3",
                "estimated_duration_seconds": 4.0,
                "shots": [
                    {
                        "number": 5,
                        "scene_number": 3,
                        "duration_seconds": 4.0,
                        "shot_size": "medium shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "Both characters perform a simple repair action.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر", "نادر"],
                        "action": "يعيدان توصيل السلك بهدوء.",
                        "emotion": "تعاون",
                        "dialogue_line_orders": [],
                        "visual_prompt": "Stylized simple repair action at the centered workbench.",
                        "animation_notes": ["Avoid complex hand close-ups."],
                        "continuity_requirements": ["Keep the storm window camera-left."],
                        "transition": "cut",
                    }
                ],
            },
            {
                "scene_number": 4,
                "title": "مشهد 4",
                "estimated_duration_seconds": 8.0,
                "shots": [
                    {
                        "number": 6,
                        "scene_number": 4,
                        "duration_seconds": 4.0,
                        "shot_size": "medium close-up",
                        "camera_angle": "eye level",
                        "camera_movement": "slow push",
                        "composition": "Warm light reaches both faces.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر", "نادر"],
                        "action": "يضيء المصباح وجهيهما.",
                        "emotion": "فرح",
                        "dialogue_line_orders": [1],
                        "visual_prompt": "Warm emergency lamp lighting both faces during the storm.",
                        "animation_notes": ["Use a gentle light change."],
                        "continuity_requirements": ["Keep the storm visible outside."],
                        "transition": "cut",
                    },
                    {
                        "number": 7,
                        "scene_number": 4,
                        "duration_seconds": 4.0,
                        "shot_size": "wide shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked-off",
                        "composition": "Final workshop tableau with warm light.",
                        "location": "الورشة الرئيسية",
                        "characters": ["عمر", "نادر"],
                        "action": "يبتسمان بجوار المصباح.",
                        "emotion": "ارتياح",
                        "dialogue_line_orders": [],
                        "visual_prompt": "Final warm workshop tableau with the storm outside.",
                        "animation_notes": ["Hold the final pose."],
                        "continuity_requirements": ["Preserve all approved details."],
                        "transition": "cut",
                    },
                ],
            },
        ],
        "global_visual_notes": ["Warm workshop palette."],
        "continuity_notes": ["Keep wardrobe stable."],
        "production_risks": ["Keep motion simple."],
    }
    original = deepcopy(payload)
    request = DirectionGenerationRequest(
        min_shot_duration_seconds=3.5,
        max_shot_duration_seconds=4.0,
        target_shot_count=10,
        max_dialogue_lines_per_shot=1,
    )

    repaired = reconcile_constrained_direction(payload, _script(), _characters(), request)
    direction = EpisodeDirection.model_validate(repaired)
    shots = [shot for scene in direction.scenes for shot in scene.shots]

    assert payload == original
    assert len(direction.scenes) == 4
    assert len(shots) == 10
    assert direction.total_estimated_duration_seconds == 40.0
    assert all(shot.duration_seconds == 4.0 for shot in shots)
    assert [scene.scene_number for scene in direction.scenes] == [1, 2, 3, 4]
    for scene in direction.scenes:
        assert [shot.number for shot in scene.shots] == list(range(1, len(scene.shots) + 1))
        assert all(shot.scene_number == scene.scene_number for shot in scene.shots)

    dialogue_refs = [
        (scene.scene_number, order)
        for scene in direction.scenes
        for shot in scene.shots
        for order in shot.dialogue_line_orders
    ]
    assert sorted(dialogue_refs) == [(1, 1), (2, 1), (4, 1)]
