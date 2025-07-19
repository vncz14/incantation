<template>
  <div id="root">
    <Navbar />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
#root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>