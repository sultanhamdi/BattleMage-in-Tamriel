# Level 3: The Canvas (User Design) - Expanded & Padded
# Size: 110x40 (Original 100 + 10 padding)
# Template: Hollow Box with Center Markers + 5 Layer Wall Padding

level_data = [
    "#####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#####",
    "#####X                                                                                                        ",
    "#####X                                                                                                       F",
    "#####X                                                                                                        ",
    "#####X                                                                                                  XXXXXX",
    "#####X                                      XXXXX                                                     XX######",
    "#####X                                       ====XXX                   XXXX                     XXXXXX==######",
    "#####X                  XXXXX        XXX     =======XX                X====XX                   ========######",
    "#####X                   ===       XX==       ========XXXXX          X=======XXXX               ========######",
    "#####X                    =        ==          ===========           ============XXX           X========######",
    "#####X                             =               =====            X===============XXX       X=========######",
    "#####X     XXXXX                                                    ===================XXXXXXX==========######",
    "#####X      ===                                                       ==================================######",
    "#####X       =                                V                        =================================######",
    "#####X                                                                  ================================######",
    "#####X                                   XXXXXXXXXXX                      ==============================######",
    "#####XX                                  ===========                       =============================######",
    "#####X=X                                ============                         ===========================######",
    "#####X==                               =============                          ==========================######",
    "#####X==X                              =============                             =======================######",
    "#####X=XXXXXXXXXXXXXXXXXXXXXXXXXX     ==============     XXXXXXXXXXX               =====================######",
    "#####X===========================     =============      ===========                 ===================######",
    "#####X===========================     =============     ============X                 ==================######",
    "#####X ===========================   =============     ==============X                    ==============######",
    "#####X   ========================== =============     ================X                      ===========######",
    "#####X    ======================== ==============    ===     ==========                        =========######",
    "#####X    ======================   =============    ====       ========X                        ========######",
    "#####X     =====================     ===========   ====          =======X          G                ====######",
    "#####X      ==================       ===========   ====          ========                             ==######",
    "#####X      ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ          X#####",
    "#####X                                                                                                  X#####",
    "#####X                                                                                                  X#####",
    "#####X                                                                                                  X#####",
    "#####X                                                                                                  X#####",
    "#####X                                                                                             XXXXXX#####",
    "#####X                                                                                                  X#####",
    "#P                                                                                                      X#####",
    "#                                                                                                       X#####",
    "#                                                                                                       X#####",
    "#_______________________________________________________________________________________________________X#####",
    "#####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#####",
]

# ===========================================
# ENEMY SPAWN CONFIGURATION - LEVEL 3
# ===========================================
# ZOMBIE APOCALYPSE! - Massive horde with mini bosses
# Setiap huruf Z di row 29 akan spawn 10 zombie (total 880 zombie!)
enemy_spawn_config = [
    ('Z', 10),  # 10 zombies per spawn point (88 spawn points = 880 zombies!)
    ('V', 2),   # 2 vampires spawn di huruf V (row 13)
    ('G', 1),   # 1 golem spawn di huruf G (row 27)
]
