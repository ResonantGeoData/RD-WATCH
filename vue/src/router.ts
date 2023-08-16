import { createRouter, createWebHashHistory } from "vue-router";

import RGD from './views/RGD.vue';
import Annotation from './views/AnnotationViewer.vue';
import { ApiService } from './client/services/ApiService'; // Import your ApiService implementation

const routes = [
  { path: '/:region?/:selected?', component: RGD, props:true, },
  { path: '/annotation/:region?/:selected?', component: Annotation, props:true, },
  { path: '/scoring/:region?/:selected?', component: RGD, props:true, },
  { path: '/scoring/annotation/:region?/:selected?', component: Annotation, props:true, },
]

const router = createRouter({
    // 4. Provide the history implementation to use. We are using the hash history for simplicity here.
    history: createWebHashHistory(),
    routes, // short for `routes: routes`
  })
  
router.beforeEach((to, from, next) => {
    // Check if the current route has a prefix '/scoring'
    const isScoringRoute = to.path.startsWith('/scoring');
  
    // Set the ApiService prefix URL accordingly
    ApiService.setApiPrefix(isScoringRoute ? "/api/scoring" : "/api");
  
    next(); // Continue with the navigation
  });
  
export default router;