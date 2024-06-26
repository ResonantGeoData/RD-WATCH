import { createApp } from "vue";
import "./index.css";
import App from "./App.vue";
import PopupComponent from "./components/PopUpComponent.vue";
import { PopUpData, PopUpSiteData } from './interactions/popUpType';
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader
import router from './router';
const vuetify = createVuetify({
  components,
  directives,
})

createApp(App).use(vuetify).use(router).mount('#app')


const createPopup = (data: Record<string, PopUpData>, siteData: Record<string, PopUpSiteData>) =>  {
return createApp(PopupComponent, {data, siteData}).use(vuetify);
}

export default createPopup;
