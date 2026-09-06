using Workerd = import "/workerd/workerd.capnp";
const config :Workerd.Config = (
  services = [(name = "pairing", worker = (
    modules = [
      (name = "pairing.mjs", esModule = embed "worker-pairing.mjs"),
      (name = "app.mjs", esModule = embed "../dist/server/index.js")
    ],
    compatibilityDate = "2025-01-01"
  ))]
);
