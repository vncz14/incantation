// https://nuxt.com/docs/api/configuration/nuxt-config

import { definePreset } from "@primevue/themes";
import Aura from "@primeuix/themes/aura";

export default defineNuxtConfig({
    css: ["@/assets/globals.css"],

    modules: ["@primevue/nuxt-module", "@nuxt/fonts"],

    fonts: {
        defaults: { weights: [400, 700], styles: ["normal", "italic"] },
        families: [{ name: "Pretendard", provider: "local" }],
    },

    primevue: {
        components: {
            prefix: "Pv",
            exclude: ["Form", "FormField"],
        },
        options: {
            theme: {
                preset: definePreset(Aura, {
                    semantic: {
                        primary: {
                            50: "{fuchsia.50}",
                            100: "{fuchsia.100}",
                            200: "{fuchsia.200}",
                            300: "{fuchsia.300}",
                            400: "{fuchsia.400}",
                            500: "{fuchsia.500}",
                            600: "{fuchsia.600}",
                            700: "{fuchsia.700}",
                            800: "{fuchsia.800}",
                            900: "{fuchsia.900}",
                            950: "{fuchsia.950}",
                        },
                    },
                }),
            },
        },
    },

    compatibilityDate: "2025-05-15",
    devtools: { enabled: true },
});
