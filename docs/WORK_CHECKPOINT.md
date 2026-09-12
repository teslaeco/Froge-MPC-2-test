# E15 handoff — R14 likeness restored; Meshy comparison delivered

2026-09-12. R15 explicitly rejected by user as critical head-size/likeness regression. E15 built from preserved R14, not R15. Head/face/eyes/teeth/body geometry, transforms and UV unchanged fromR14 (55protectedmeshSHA checks). Only312hairguides modified:radius22%smaller, outerexcesscompressed35%, overallhairwidth9.1%narrower;mattehairresponse. This corrects regression and hairbulk, NOT a new faithful reconstruction. BaselineR14/R15 preserved.

ActualfinalFBXreimport:1,990,254evaluatedtriangles,420mesh objects allUV,2eyeobjects,0missingimage data. FBXSHA256639eb17dfb2835467eac1d13ef6f50c6b1599ee34ffb72d5be09078f3e49c5c1. AllsixFBXrendersnewerthanasset; checkedfinalface/front/side/back/clay andcomparison sheets. Initial rawcountmissed324modifiertriangles; assertioncaughtit, evaluatedsourcecountverifiedandbuild.pyfixed.

Sevenuserdeliverablessaved successfully(localmetadata true), identities in docs/reviews/correction-e15/saved-artifacts.json:FORGE-model-E15.blend/.fbx/.glb,FORGE-R14-R15-E15.png,FORGE-E15-trzy-widoki.png,FORGE-E15-vs-Meshy.png,POROWNANIE-E15-Meshy.md. ManifesthasSHA/bytes. Re-deliverthese onchatfailureinstead ofregenerating.

Comparisonconclusion:Meshy wins thiscase inlikeness, sculptedeyes/nose/mouth/neck, integratedhairmass andgarmentconstruction. Ourclayreviewexposesheavyrelianceonphotographictexture; geometryitselfinsufficient. MeshyassessmentbasedONLYontwouser screenshots, differentcameras/lighting/scales;3,057,126trianglesaccordingUI, rawMeshyunavailable. Notopo/UV/print/speed/costclaims aboutMeshy. E15stillhasR14nosalopening/mouthboundary/haircap/neckproblems andisnotacceptedphotorealisticorprintready. NoOracle/Sitedeployments,paidMeshygenerationorquota changes.

Sources docs/reviews/correction-e15. Runbuild.py onR14,render.py onactualexport,compose.py forsheets. Sourcecheckpointbeforehandoff3c2d265cc5e8b394dfd820de433f2343c642b813. FinalanswershowR14/R15/E15,threeviewsandMeshycomparison,modeldownloadlinks,plainhonestconclusion.
