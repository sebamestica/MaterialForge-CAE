# TPMS Geometry Validation Report
Generated: 2026-06-09 22:03:21

| Pattern | Vertices | Faces | Gen Time (s) | Watertight | Valid Volume |
| --- | --- | --- | --- | --- | --- |
| Diamond | 110065 | 226114 | 2.360 | True | True |
| Diamond TPMS | 110065 | 226114 | 2.372 | True | True |
| Gyroid | 98911 | 200766 | 2.395 | True | True |
| Honeycomb | 83425 | 167526 | 1.943 | True | True |
| Schwarz P | 87421 | 176922 | 2.357 | True | True |
| tpms_graded | 95565 | 194278 | 2.264 | True | True |

### Verification Summary
- **Watertightness**: Verifies that the solid volume is completely closed without open holes.
- **Valid Volume**: Ensures the mesh is manifold, correctly oriented, and computes a positive physical volume.
- **Generation Time**: Measures the geometry compilation latency (limit: < 2.0 seconds).