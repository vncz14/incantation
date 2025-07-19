<template>
    <div class="not-found-container">
        <h1>404</h1>
        <NuxtLink to="/">
            <PvButton label="Go Home" />
        </NuxtLink>
    </div>
</template>

<style scoped>

.not-found-container {
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
}

h1 {
    font-size: 3rem;
}

</style>
