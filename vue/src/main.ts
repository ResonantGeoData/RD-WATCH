import { createApp } from "vue";
import "./index.css";
import App from "./App.vue";
import { map } from "./map";
map.on("load", () => createApp(App).mount("#app"));
