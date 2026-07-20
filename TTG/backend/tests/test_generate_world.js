// test_generate_world.js
const { io } = require("socket.io-client");

// connect to NORMAL socket namespace (not /engine)
const socket = io("http://localhost:3000", {
  auth: {
    token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX3doYWMiLCJyb2xlcyI6WyJ1c2VyIl0sImlhdCI6MTc2OTA1OTE4MywiZXhwIjoxNzY5MDYyNzgzLCJpc3MiOiJtaWNyb2JyaWRnZS5pbnRlcm5hbCJ9.cxGgJ8t2Sp8TBdQ5vPRROfjLCRROuMGBLouu3llWb9w"
  }
});

socket.on("connect", () => {
  console.log("[TEST GENERATE WORLD] connected:", socket.id);

  // Emit generate_world with SCHEMA-VALID payload
  socket.emit("generate_world", {
    config: {
      schema_version: "1.0",

      world: {
        id: "world_test",
        name: "Test World",
        gravity: [0, -9.8, 0]
      },

      scene: {
        id: "scene_test",
        ambientLight: [1, 1, 1],
        skybox: "default"
      },

      entities: [
        {
          id: "player_1",
          type: "player",

          transform: {
            position: [0, 0, 0],
            rotation: [0, 0, 0],
            scale: [1, 1, 1]
          },

          material: {
            shader: "basic",
            texture: "player.png",
            color: [1, 1, 1]
          },

          components: {
            mesh: "player_mesh",
            collider: "box",
            script: "playerController"
          }
        }
      ],

      quests: [
        {
          id: "quest_1",
          triggerEntity: "player_1",
          goal: "Reach the checkpoint"
        }
      ]
    },
    submittedAt: Date.now()
  });

  console.log("[TEST GENERATE WORLD] generate_world emitted");
});

socket.on("disconnect", () => {
  console.log("[TEST GENERATE WORLD] disconnected");
});
