<template>
    <div class='tool-detail' v-if="selected" :style="{'--detailRight': detailRight, '--detailArrow': detailArrow}">
        <div v-show="IS_DM">Mode</div>
        <div v-show="IS_DM" class='selectgroup'>
            <div
                v-for="mode in modes"
                :key="mode"
                class='option'
                :class="{'option-selected': modeSelect === mode}"
                @click="modeSelect = mode"
            >
                {{ mode }}
            </div>
        </div>
        <div>Shape</div>
        <div class='selectgroup'>
            <div
                v-for="shape in shapes"
                :key="shape"
                class='option'
                :class="{'option-selected': shapeSelect === shape}"
                @click="shapeSelect = shape"
            >
                <i class="fas" :class="'fa-' + shape"></i>
            </div>
        </div>
        <div>Colours</div>
        <div class='selectgroup'>
            <color-picker class='option' :color.sync="fillColour" />
            <color-picker class='option' :color.sync="borderColour" />
        </div>
        <div v-show='shapeSelect === "paint-brush"'>Brush size</div>
        <input type='text' v-model='brushSize' v-show='shapeSelect === "paint-brush"' style='max-width:100px;'>
    </div>
</template>

<script lang="ts">
import { mapState } from "vuex";

import colorpicker from "../../../core/components/colorpicker.vue";
import gameManager from "../../manager";
import Circle from "../../shapes/circle";
import MultiLine from "../../shapes/multiline";
import Rect from "../../shapes/rect";
import Shape from "../../shapes/shape";
import store from "../../store";
import Tool from "./tool.vue";

import { socket } from "../../comm/socket";
import { GlobalPoint } from "../../geom";
import { FOWLayer } from "../../layers/fow";
import { getUnitDistance, l2g } from "../../units";
import { getMouse } from "../../utils";

const tempUnitSize = store.state.unitSize;

export default Tool.extend({
    components: {
        "color-picker": colorpicker,
    },
    data: () => ({
        name: "Draw",
        active: false,

        startPoint: <GlobalPoint | null>null,
        shape: <Shape | null>null,
        brushHelper: <Circle | null>null,

        fillColour: "rgba(0, 0, 0, 1)",
        borderColour: "rgba(255, 255, 255, 0)",

        shapeSelect: "square",
        shapes: ["square", "circle", "paint-brush"],
        modeSelect: "normal",
        modes: ["normal", "reveal", "hide"],

        brushSize: getUnitDistance(tempUnitSize),
    }),
    computed: {
        helperSize(): number {
            if (this.shapeSelect === "paint-brush") return this.brushSize / 2;
            return getUnitDistance(this.unitSize) / 8;
        },
        IS_DM(): boolean {
            return this.$store.state.IS_DM;
        },
        unitSize(): number {
            return this.$store.state.unitSize;
        },
        useGrid(): boolean {
            return this.$store.state.useGrid;
        },
    },
    watch: {
        fillColour() {
            if (this.brushHelper) this.brushHelper.fillColour = this.fillColour;
        },
        modeSelect(newValue, oldValue) {
            this.onModeChange(newValue, oldValue);
        },
    },
    methods: {
        setupBrush() {
            if (this.brushHelper === null) return;
            if (this.modeSelect === "reveal" || this.modeSelect === "hide") {
                this.brushHelper.options.set("preFogShape", true);
                this.brushHelper.options.set("skipDraw", true);
                this.brushHelper.fillColour = "rgba(0, 0, 0, 1)";

                if (this.modeSelect === "reveal") this.brushHelper.globalCompositeOperation = "source-over";
                else if (this.modeSelect === "hide") this.brushHelper.globalCompositeOperation = "destination-out";
            } else {
                this.brushHelper.options.delete("preFogShape");
                this.brushHelper.options.delete("skipDraw");
                this.brushHelper.globalCompositeOperation = "source-over";
                this.brushHelper.fillColour = this.fillColour;
            }
        },
        onModeChange(newValue: string, oldValue: string) {
            if (this.brushHelper === null) return;

            const fowLayer = gameManager.layerManager.getLayer("fow");
            const normalLayer = gameManager.layerManager.getLayer();
            if (fowLayer === undefined || normalLayer === undefined) return;

            this.setupBrush();

            if (newValue !== "normal" && oldValue === "normal") {
                normalLayer.removeShape(this.brushHelper, false);
                fowLayer.addShape(this.brushHelper, false);
            } else if (newValue === "normal" && oldValue !== "normal") {
                normalLayer.addShape(this.brushHelper, false);
                fowLayer.removeShape(this.brushHelper, false);
            }
        },
        getLayer() {
            if (this.modeSelect === "normal") return gameManager.layerManager.getLayer();
            return gameManager.layerManager.getLayer("fow");
        },
        onMouseDown(event: MouseEvent) {
            const layer = this.getLayer();
            if (layer === undefined) {
                console.log("No active layer!");
                return;
            }
            this.active = true;
            this.startPoint = l2g(getMouse(event));
            if (this.shapeSelect === "square")
                this.shape = new Rect(this.startPoint.clone(), 0, 0, this.fillColour, this.borderColour);
            else if (this.shapeSelect === "circle")
                this.shape = new Circle(this.startPoint.clone(), this.helperSize, this.fillColour, this.borderColour);
            else if (this.shapeSelect === "paint-brush") {
                this.shape = new MultiLine(this.startPoint.clone(), [], this.brushSize);
                this.shape.fillColour = this.fillColour;
            } else return;

            if (this.modeSelect !== "normal") {
                this.shape.options.set("preFogShape", true);
                this.shape.options.set("skipDraw", true);
                this.shape.fillColour = "rgba(0, 0, 0, 1)";
            }
            if (this.modeSelect === "reveal") this.shape.globalCompositeOperation = "source-over";
            else if (this.modeSelect === "hide") this.shape.globalCompositeOperation = "destination-out";

            this.shape.owners.push(this.$store.state.username);
            if (layer.name === "fow" && this.modeSelect === "normal") {
                this.shape.visionObstruction = true;
                this.shape.movementObstruction = true;
            }
            gameManager.visionBlockers.push(this.shape.uuid);
            layer.addShape(this.shape, true, false);

            // Push brushhelper to back
            this.onDeselect();
            this.onSelect();
        },
        onMouseMove(event: MouseEvent) {
            const endPoint = l2g(getMouse(event));
            const layer = this.getLayer();
            if (layer === undefined) {
                console.log("No active layer!");
                return;
            }

            if (this.brushHelper !== null) {
                this.brushHelper.r = this.helperSize;
                this.brushHelper.refPoint = endPoint;
                if (!this.active) layer.invalidate(false);
            }

            if (!this.active || this.startPoint === null || this.shape === null) return;

            if (this.shapeSelect === "square") {
                (<Rect>this.shape).w = Math.abs(endPoint.x - this.startPoint.x);
                (<Rect>this.shape).h = Math.abs(endPoint.y - this.startPoint.y);
                this.shape.refPoint.x = Math.min(this.startPoint.x, endPoint.x);
                this.shape.refPoint.y = Math.min(this.startPoint.y, endPoint.y);
            } else if (this.shapeSelect === "circle") {
                (<Circle>this.shape).r = endPoint.subtract(this.startPoint).length();
            } else if (this.shapeSelect === "paint-brush") {
                (<MultiLine>this.shape).points.push(endPoint);
            }
            socket.emit("Shape.Update", { shape: this.shape!.asDict(), redraw: true, temporary: false });
            if (this.shape.visionObstruction) gameManager.recalculateBoundingVolume();
            layer.invalidate(false);
        },
        onMouseUp(event: MouseEvent) {
            if (this.active && this.shape !== null && !event.altKey && this.useGrid) {
                this.shape.resizeToGrid();
                socket.emit("Shape.Update", { shape: this.shape!.asDict(), redraw: true, temporary: false });
            }
            this.active = false;
        },
        onSelect() {
            const layer = this.getLayer();
            if (layer === undefined) return;
            this.brushHelper = new Circle(new GlobalPoint(-1000, -1000), this.brushSize / 2, this.fillColour);
            this.setupBrush();
            layer.addShape(this.brushHelper, false); // during mode change the shape is already added
        },
        onDeselect() {
            const layer = this.getLayer();
            if (this.brushHelper !== null && layer !== undefined) layer.removeShape(this.brushHelper, false);
        },
    },
});
</script>

<style scoped>
.option {
    padding: 6px;
    border: solid 1px #82c8a0;
    border-radius: 0;
    flex: 1 1;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 13px;
    min-width: 25px;
}
.option-selected,
.option:hover {
    background-color: #82c8a0;
}
.selectgroup {
    display: flex;
}
.selectgroup > .option:first-of-type {
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
}
.selectgroup > .option:last-of-type {
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}
</style>
