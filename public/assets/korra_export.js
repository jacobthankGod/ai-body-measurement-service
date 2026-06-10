/**
 * KORRA Export Engine | Phase 5: Multi-Angle Intelligence
 * ====================================================
 * High-fidelity PDF and Image extraction suite.
 */

window.KORRA_EXPORT = {
    pdf: function(clientName, measurements, gender, height) {
        console.log("📄 Generating Clinical PDF...");
        const doc = new jspdf.jsPDF();

        // Brand Header
        doc.setFillColor(0, 0, 0);
        doc.rect(0, 0, 210, 40, 'F');
        doc.setTextColor(87, 215, 192); // Mint
        doc.setFontSize(24);
        doc.text("KORRA", 20, 25);
        doc.setFontSize(10);
        doc.text("BIOMETRIC PASSPORT / CLINICAL GRADE", 20, 32);

        // Subject Info
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(16);
        doc.text(`Subject: ${clientName}`, 20, 55);
        doc.setFontSize(10);
        doc.text(`Protocol: ±1cm Precision AI Extraction`, 20, 62);
        doc.text(`Gender: ${gender} | Height: ${height}cm`, 20, 68);
        doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, 74);

        // Measurements Table
        let y = 90;
        doc.setFontSize(12);
        doc.setTextColor(80, 80, 80);

        Object.entries(measurements).forEach(([key, val]) => {
            if (typeof val === 'number') {
                doc.text(`${key}:`, 20, y);
                doc.setTextColor(0, 0, 0);
                doc.text(`${val} cm`, 150, y);
                doc.setTextColor(80, 80, 80);
                y += 10;
                if (y > 270) { doc.addPage(); y = 20; }
            }
        });

        doc.save(`korra_passport_${clientName.replace(/\s+/g, '_')}.pdf`);
    },

    /**
     * PHASE 5: MULTI-ANGLE SNAPSHOTS
     * Captures 4 angles from a given visualizer instance.
     */
    captureMultiAngle: async function(viz, clientName) {
        console.log("📸 Executing Multi-Angle Forensic Capture...");
        const angles = [
            { name: 'Front', y: Math.PI },
            { name: 'Back', y: 0 },
            { name: 'Left', y: Math.PI / 2 },
            { name: 'Right', y: -Math.PI / 2 }
        ];

        const zip = []; // For now we'll just download 4 files or one combined PDF
        const originalRotation = viz.mesh.rotation.y;
        viz.isInteracting = true; // Pause auto-rotate

        const doc = new jspdf.jsPDF('l', 'mm', 'a4');
        doc.setFillColor(0, 0, 0);
        doc.rect(0, 0, 297, 210, 'F');
        doc.setTextColor(87, 215, 192);
        doc.text(`DIAGNOSTIC REPORT: ${clientName}`, 10, 15);

        for (let i = 0; i < angles.length; i++) {
            viz.mesh.rotation.y = angles[i].y;
            viz.renderer.render(viz.scene, viz.camera);
            const imgData = viz.renderer.domElement.toDataURL('image/png');

            const x = 10 + (i * 70);
            doc.addImage(imgData, 'PNG', x, 30, 65, 120);
            doc.setFontSize(8);
            doc.text(angles[i].name, x + 25, 160);
        }

        viz.mesh.rotation.y = originalRotation;
        viz.isInteracting = false;
        doc.save(`korra_diagnostic_${clientName}.pdf`);
    },

    obj: function(url, name) {
        if(!url) return;
        const link = document.createElement('a');
        link.href = url;
        link.download = `korra_mesh_${name}.obj`;
        link.click();
    }
};
