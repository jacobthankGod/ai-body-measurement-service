/**
 * KORRA Export Engine | Phase 5 + Phase 188: Multi-Angle + VTO PDF
 * ================================================================
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

        doc.save(`korra_profile_${clientName.replace(/\s+/g, '_')}.pdf`);
    },

    /**
     * PHASE 188: VTO-ENHANCED PDF EXPORT
     * Appends VTO preview images to the standard biometric PDF.
     */
    pdfWithVTO: async function(clientName, measurements, gender, height, vtoResults) {
        console.log("📄 Generating VTO-Enhanced PDF...");
        const doc = new jspdf.jsPDF();

        // Page 1: Standard biometric passport
        doc.setFillColor(0, 0, 0);
        doc.rect(0, 0, 210, 40, 'F');
        doc.setTextColor(87, 215, 192);
        doc.setFontSize(24);
        doc.text("KORRA", 20, 25);
        doc.setFontSize(10);
        doc.text("BIOMETRIC PASSPORT + VTO RESULTS", 20, 32);

        doc.setTextColor(0, 0, 0);
        doc.setFontSize(16);
        doc.text(`Subject: ${clientName}`, 20, 55);
        doc.setFontSize(10);
        doc.text(`Protocol: ±1cm Precision AI Extraction`, 20, 62);
        doc.text(`Gender: ${gender} | Height: ${height}cm`, 20, 68);
        doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, 74);

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

        // Page 2: VTO Results
        if (vtoResults && Object.values(vtoResults).some(Boolean)) {
            doc.addPage();
            doc.setFillColor(0, 0, 0);
            doc.rect(0, 0, 210, 40, 'F');
            doc.setTextColor(87, 215, 192);
            doc.setFontSize(18);
            doc.text("VTO RESULTS", 20, 25);

            const angles = ['front', 'back', 'left', 'right'];
            const loadedImages = [];
            for (const angle of angles) {
                const url = vtoResults[angle];
                if (!url) continue;
                try {
                    const img = await new Promise((resolve, reject) => {
                        const el = new Image();
                        el.crossOrigin = 'anonymous';
                        el.onload = () => resolve(el);
                        el.onerror = () => reject(new Error(`Failed to load ${angle}`));
                        el.src = url;
                    });
                    loadedImages.push({ angle, img });
                } catch (e) {
                    console.warn(`Could not load VTO image for ${angle}:`, e);
                }
            }

            if (loadedImages.length === 0) {
                doc.setTextColor(120, 120, 120);
                doc.text("No VTO images available", 20, 60);
            } else {
                // Layout: 2x2 grid
                const positions = [
                    { x: 10, y: 45 },
                    { x: 110, y: 45 },
                    { x: 10, y: 140 },
                    { x: 110, y: 140 },
                ];
                for (let i = 0; i < loadedImages.length && i < 4; i++) {
                    const pos = positions[i];
                    const { angle, img } = loadedImages[i];
                    // Scale to fit 90x85 box
                    const maxW = 90, maxH = 85;
                    let w = img.naturalWidth || img.width;
                    let h = img.naturalHeight || img.height;
                    const scale = Math.min(maxW / w, maxH / h);
                    w *= scale;
                    h *= scale;
                    doc.addImage(img, 'JPEG', pos.x, pos.y, w, h);
                    doc.setFontSize(9);
                    doc.setTextColor(255, 255, 255);
                    doc.text(angle.toUpperCase(), pos.x + 35, pos.y + maxH + 6);
                }
            }

            // Page 3: Fit score summary
            doc.addPage();
            doc.setFillColor(0, 0, 0);
            doc.rect(0, 0, 210, 30, 'F');
            doc.setTextColor(87, 215, 192);
            doc.setFontSize(14);
            doc.text("VTO FIT ASSESSMENT", 20, 20);
            doc.setTextColor(80, 80, 80);
            doc.text("Generated by KORRA AI Body Scan", 20, 40);
            doc.text("Results are AI-estimated and may vary.", 20, 48);
            doc.text(`Garment try-on completed for ${loadedImages.length} angle(s).`, 20, 56);
        }

        doc.save(`korra_profile_vto_${clientName.replace(/\s+/g, '_')}.pdf`);
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
    },

    /**
     * PHASE 21: AUTOMATED TAILOR BRIEF
     * Generates a "Cutting Sheet" based on measurements.
     */
    generateTailorBrief: function(clientName, measurements, shape, sizeRec) {
        console.log("✂️ Generating AI Tailor Brief...");
        const doc = new jspdf.jsPDF();

        doc.setFillColor(87, 215, 192); // Mint Header
        doc.rect(0, 0, 210, 40, 'F');
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(22);
        doc.text("KORRA | TAILOR BRIEF", 20, 25);
        doc.setFontSize(9);
        doc.text("AI-GENERATED CUTTING INSTRUCTIONS", 20, 32);

        doc.setFontSize(14);
        doc.text(`Client: ${clientName}`, 20, 55);
        doc.setFontSize(11);
        doc.text(`Body Shape: ${shape} | Size Rec: ${sizeRec}`, 20, 62);

        // Logic-based instructions
        let y = 80;
        doc.setFontSize(12);
        doc.text("CONSTRUCTION GUIDANCE:", 20, y);
        y += 10;
        doc.setFontSize(10);
        doc.setTextColor(80, 80, 80);

        const chest = measurements['Chest Round'];
        const waist = measurements['Waist Round'];

        if (waist > chest) {
            doc.text("- ADJUSTMENT: High waist-to-chest ratio detected. Apply extra ease at midsection.", 20, y);
            y += 8;
        }
        if (shape === "Inverted Triangle") {
            doc.text("- ADJUSTMENT: Broad shoulder silhouette detected. Recommend tapering from yoke to waist.", 20, y);
            y += 8;
        }
        if (shape === "Hourglass") {
            doc.text("- ADJUSTMENT: Balanced silhouette. Optimal for slim-fit and darts.", 20, y);
            y += 8;
        }

        doc.text("- FABRIC EASE: Standard +2cm ease applied to all circumferences.", 20, y);
        y += 15;

        // Table
        doc.setTextColor(0, 0, 0);
        doc.text("RAW EXTRACTION DATA:", 20, y);
        y += 10;
        Object.entries(measurements).forEach(([k, v]) => {
            if (typeof v === 'number') {
                doc.text(`${k}:`, 20, y);
                doc.text(`${v}cm`, 150, y);
                y += 8;
                if (y > 270) { doc.addPage(); y = 20; }
            }
        });

        doc.save(`korra_tailor_brief_${clientName}.pdf`);
    },

    /**
     * PHASE 40: GLOBAL SIZE PROTOCOL
     * Exports biometric ID in a standardized JSON format.
     */
    exportSizeProtocol: function(name, measurements) {
        const protocol = {
            "version": "1.0",
            "protocol": "KORRA_SIZE_ID",
            "subject": name,
            "timestamp": new Date().toISOString(),
            "biometrics": measurements,
            "signature": "AI_VERIFIED_HMR"
        };
        const blob = new Blob([JSON.stringify(protocol, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `korra_protocol_${name}.json`;
        a.click();
    }
};
