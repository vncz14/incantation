<template>
    <PvMenubar :model="items" 
    :style="{
        borderRadius: 0,
        border: 0,
    }">
        <template #start>
            <NavbarLogo />
        </template>
        <template #end>
            <Avatar />
        </template>
    </PvMenubar>
</template>

<script setup>
const items = ref([
    {

    }
]);
</script>

<style scoped>

</style>