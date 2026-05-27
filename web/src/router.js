import { createRouter, createWebHashHistory } from "vue-router";
import HomeView from "@/views/HomeView.vue";
import ExamView from "@/views/ExamView.vue";
import TrainingView from "@/views/TrainingView.vue";
import MistakesView from "@/views/MistakesView.vue";
import SrsView from "@/views/SrsView.vue";
import StatsView from "@/views/StatsView.vue";
import ResultView from "@/views/ResultView.vue";
import BrowseView from "@/views/BrowseView.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/exam", name: "exam", component: ExamView },
    { path: "/training", name: "training", component: TrainingView },
    { path: "/mistakes", name: "mistakes", component: MistakesView },
    { path: "/srs", name: "srs", component: SrsView },
    { path: "/browse", name: "browse", component: BrowseView },
    { path: "/stats", name: "stats", component: StatsView },
    { path: "/result", name: "result", component: ResultView },
  ],
});

export default router;
