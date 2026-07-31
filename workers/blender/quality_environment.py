from quality_common import material, set_material, set_scale


def upgrade():
    plaster = material("Q_Plaster", (0.29, 0.34, 0.42, 1), 0.82)
    wood = material("Q_Wood", (0.30, 0.12, 0.04, 1), 0.52)
    dark_wood = material("Q_DarkWood", (0.075, 0.028, 0.016, 1), 0.62)
    teal = material("Q_Teal", (0.018, 0.28, 0.33, 1), 0.48)
    navy = material("Q_Navy", (0.018, 0.045, 0.13, 1), 0.52)
    orange = material("Q_Orange", (0.76, 0.20, 0.03, 1), 0.48)
    for name in ("ENV_BackWall", "ENV_LeftWall", "ENV_RightWall"):
        set_material(name, plaster)
    set_material("ENV_Floor", dark_wood)
    set_material("ENV_WorkbenchTop", wood)
    set_material("Omar_Torso", teal)
    set_material("Nader_Torso", navy)
    set_material("Nader_Shirt", orange)
    set_scale("Omar_Torso", (0.92, 0.96, 0.94), 0.10)
    set_scale("Nader_Torso", (0.88, 0.94, 0.90), 0.10)
    for char in ("Omar", "Nader"):
        for part in ("UpperArm_L", "UpperArm_R", "Forearm_L", "Forearm_R"):
            set_scale(f"{char}_{part}", (0.88, 0.92, 0.90), 0.07)
