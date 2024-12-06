import { createRouter, createWebHashHistory } from "vue-router";

import RGD from './views/RGD.vue';
import Annotation from './views/AnnotationViewer.vue';
import FullScreenImageViewer from './views/FullScreenImageViewer.vue';
import SAM from './views/SAM.vue';
import SmartFlow from "./views/SmartFlow.vue";
import IQR from "./views/IQR.vue";

const routes = [
  { path: '/imageViewer/:siteEvalId', component: FullScreenImageViewer, props:true, },
  { path: '/scoring/imageViewer/:siteEvalId', component: FullScreenImageViewer, props:true, },
  { path: '/scoring/:region?/:selected?', component: RGD, props:true, },
  { path: '/scoring/proposals/:region?/:selected?', component: Annotation, props:true, },
  { path: '/:region?/:selected?', component: RGD, props:true, },
  { path: '/proposals/:region?/:selected?', component: Annotation, props:true, },
  { path: '/SAM/:id', component: SAM, props:true, },
  { path: '/smartflow', component: SmartFlow, },
  { path: '/iqr/:region?/:selected?', component: IQR, },
]

const router = createRouter({
    // 4. Provide the history implementation to use. We are using the hash history for simplicity here.
    history: createWebHashHistory(),
    routes, // short for `routes: routes`
  })

export default router;
