import { defineStore } from 'pinia';
import { markRaw, shallowRef } from 'vue';

export const useSarHavenPanelStore = defineStore(
  'gev-sar-haven-panel',
  () => {
    const panel = shallowRef(null);
    const controls = shallowRef(null);

    function publish(next) {
      panel.value = next && markRaw(next);
    }

    function connect(next) {
      controls.value = next && markRaw(next);
    }

    return { panel, publish, controls, connect };
  },
);

