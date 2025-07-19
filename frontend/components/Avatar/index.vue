<template>
    <div v-if="!loading">
        <PvAvatar v-if="loggedIn" :label="sub.length > 0 ? sub[0] : ''" shape="circle" @click="toggleMenu" :style="{cursor: 'pointer'}"/>
        <NuxtLink v-else to="http://localhost:8000/auth/google/login">
            <PvButton label="Login with Google" icon="pi pi-user" />
        </NuxtLink>
        <PvMenu ref="menu" id="overlay_menu" :model="items" :popup="true" />
    </div>
</template>

<script setup lang="ts">

const loading = ref(true);
const loggedIn = ref(false);
const sub = ref('');

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/auth/me', {
      credentials: 'include',
    })
    if (res.ok) {
      const data = await res.json()
      loggedIn.value = true
      sub.value = data.sub
    } else {
      loggedIn.value = false
    }
  } catch {
    loggedIn.value = false
  }
  loading.value = false
})

const menu = ref();

const toggleMenu = (event: Event) => {
    menu.value.toggle(event);
};

const items = ref([
    {
        label: 'Settings',
        icon: 'pi pi-cog',
        command: () => navigateTo("/settings")
    },
    {
        label: 'Logout',
        icon: 'pi pi-sign-out',
        command: async () => {
            await fetch('http://localhost:8000/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
            loggedIn.value = false;
            sub.value = '';
            navigateTo("/");
        }
    }
]);

</script>