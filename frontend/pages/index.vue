<template>
    <div class="play-page">
        <PvButton>Create room</PvButton>
        <div class="enter-room-id">
            <PvInputText placeholder="Enter room ID" />
            <PvButton>Join room</PvButton>
        </div>
    </div>
</template>

<style scoped>

.play-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
}

.enter-room-id {
    display:flex;
    gap: 0.5rem;
}

</style>