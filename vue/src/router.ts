import { createRouter, createWebHashHistory } from "vue-router";

import RGD from './views/RGD.vue';
import Annotation from './views/Annotation.vue';

const routes = [
    { path: '/', component: RGD },
    { path: '/annotation', component: Annotation }
]

const router = createRouter({
    // 4. Provide the history implementation to use. We are using the hash history for simplicity here.
    history: createWebHashHistory(),
    routes, // short for `routes: routes`
  })
  
export default router;