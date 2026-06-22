/**
 * KORRA Heatmap GLSL Shaders | Phase 103
 * =====================================
 * Industrial standard vertex and fragment shaders for real-time ease visualization.
 */

window.KORRA_HEATMAP_SHADER = {
    vertexShader: `
        varying vec3 vPosition;
        varying float vDistance;
        uniform float uTime;

        void main() {
            vPosition = position;
            // Calculate distance from center axis (assuming Y is up)
            vDistance = length(vec2(position.x, position.z));
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        varying vec3 vPosition;
        varying float vDistance;
        uniform float uBaseRadius;
        uniform float uActiveMultiplier;
        uniform float uOpacity;

        void main() {
            // Calculate 'Ease Density' (delta between skin and fabric volume)
            // Blue (0.0) = Skin/Tight
            // Green (0.5) = Comfort/Ease
            // Red (1.0) = Loose/Voluminous

            float skinThreshold = uBaseRadius;
            float easeVal = (vDistance - skinThreshold) / (uBaseRadius * 0.5);
            easeVal = clamp(easeVal * uActiveMultiplier, 0.0, 1.0);

            vec3 colorBlue = vec3(0.0, 0.4, 1.0);
            vec3 colorGreen = vec3(0.34, 0.84, 0.75);
            vec3 colorRed = vec3(1.0, 0.2, 0.2);

            vec3 finalColor;
            if (easeVal < 0.5) {
                finalColor = mix(colorBlue, colorGreen, easeVal * 2.0);
            } else {
                finalColor = mix(colorGreen, colorRed, (easeVal - 0.5) * 2.0);
            }

            gl_FragColor = vec4(finalColor, uOpacity);
        }
    `
};
