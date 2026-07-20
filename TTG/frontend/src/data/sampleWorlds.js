export const SAMPLE_WORLDS = {
  forest: {
    "meta": {
      "game_title": "Dark Forest Runner",
      "version": "1.0"
    },
    "gameplay": {
      "game_mode": "infinite_runner",
      "movement_axis": "z",
      "global_speed": 5.0,
      "gravity": -9.8,
      "score_metric": "distance"
    },
    "camera": {
      "mode": "follow_third_person",
      "offset": [0, 3, -5],
      "look_at_offset": [0, 1, 0]
    },
    "player": {
      "start_pos": [0, 0, 0],
      "abilities": {
        "jump_force": 8.0,
        "lane_switch_speed": 4.0,
        "dash_speed": 10.0
      },
      "mesh_id": "player_cube"
    },
    "entities": [
      {
        "id": "tree_obstacle",
        "type": "obstacle",
        "mesh_id": "tree",
        "spawn_rule": {
          "spawn_rate": 0.3,
          "lane_distribution": "random",
          "y_offset": 0
        },
        "collision_effect": "game_over"
      },
      {
        "id": "coin_pickup",
        "type": "pickup",
        "mesh_id": "coin",
        "spawn_rule": {
          "spawn_rate": 0.5,
          "lane_distribution": "all",
          "y_offset": 1.0
        },
        "collision_effect": "score_add"
      }
    ]
  },
  desert: {
    "meta": {
      "game_title": "Desert Dash",
      "version": "1.0"
    },
    "gameplay": {
      "game_mode": "infinite_runner",
      "movement_axis": "z",
      "global_speed": 6.5,
      "gravity": -9.8,
      "score_metric": "distance"
    },
    "camera": {
      "mode": "follow_third_person",
      "offset": [0, 4, -6],
      "look_at_offset": [0, 1, 0]
    },
    "player": {
      "start_pos": [0, 0, 0],
      "abilities": {
        "jump_force": 9.0,
        "lane_switch_speed": 5.0,
        "dash_speed": 12.0
      },
      "mesh_id": "player_cube"
    },
    "entities": [
      {
        "id": "cactus_obstacle",
        "type": "obstacle",
        "mesh_id": "cactus",
        "spawn_rule": {
          "spawn_rate": 0.4,
          "lane_distribution": "random",
          "y_offset": 0
        },
        "collision_effect": "game_over"
      },
      {
        "id": "gem_pickup",
        "type": "pickup",
        "mesh_id": "gem",
        "spawn_rule": {
          "spawn_rate": 0.3,
          "lane_distribution": "center",
          "y_offset": 1.5
        },
        "collision_effect": "score_add"
      }
    ]
  },
  ocean: {
    "meta": {
      "game_title": "Ocean Dive",
      "version": "1.0"
    },
    "gameplay": {
      "game_mode": "side_scroller",
      "movement_axis": "x",
      "global_speed": 4.0,
      "gravity": -4.5,
      "score_metric": "time"
    },
    "camera": {
      "mode": "fixed_ortho",
      "offset": [0, 0, -10],
      "look_at_offset": [0, 0, 0]
    },
    "player": {
      "start_pos": [0, -5, 0],
      "abilities": {
        "jump_force": 6.0,
        "lane_switch_speed": 3.0,
        "dash_speed": 8.0
      },
      "mesh_id": "player_cube"
    },
    "entities": [
      {
        "id": "shark_obstacle",
        "type": "obstacle",
        "mesh_id": "shark",
        "spawn_rule": {
          "spawn_rate": 0.2,
          "lane_distribution": "random",
          "y_offset": -2.0
        },
        "collision_effect": "game_over"
      },
      {
        "id": "pearl_pickup",
        "type": "pickup",
        "mesh_id": "pearl",
        "spawn_rule": {
          "spawn_rate": 0.4,
          "lane_distribution": "all",
          "y_offset": 0
        },
        "collision_effect": "score_add"
      }
    ]
  },
  volcano: {
    "meta": {
      "game_title": "Volcano Escape",
      "version": "1.0"
    },
    "gameplay": {
      "game_mode": "infinite_runner",
      "movement_axis": "z",
      "global_speed": 7.0,
      "gravity": -9.8,
      "score_metric": "distance"
    },
    "camera": {
      "mode": "follow_third_person",
      "offset": [0, 5, -7],
      "look_at_offset": [0, 1.5, 0]
    },
    "player": {
      "start_pos": [0, 2, 0],
      "abilities": {
        "jump_force": 10.0,
        "lane_switch_speed": 6.0,
        "dash_speed": 15.0
      },
      "mesh_id": "player_cube"
    },
    "entities": [
      {
        "id": "lava_rock_obstacle",
        "type": "obstacle",
        "mesh_id": "lava_rock",
        "spawn_rule": {
          "spawn_rate": 0.5,
          "lane_distribution": "random",
          "y_offset": 0
        },
        "collision_effect": "game_over"
      },
      {
        "id": "fire_crystal_pickup",
        "type": "pickup",
        "mesh_id": "fire_crystal",
        "spawn_rule": {
          "spawn_rate": 0.35,
          "lane_distribution": "all",
          "y_offset": 2.0
        },
        "collision_effect": "score_add"
      }
    ]
  }
};
