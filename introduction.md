# Polytwisters

app created by Nathan Ho

shapes invented by Jonathan Bowers

## What is this?

This is a Web app that presents *polytwisters*, a class of strange curved shapes with four spatial dimensions discovered by amateur mathematician Jonathan Bowers. Mathematically, polytwisters are the result of combining Hopf fibration with polyhedra. As 4D objects can't be completely perceived in our world, this app uses 3D cross sections of polytwisters, just as every 3D object can be sliced by a plane to produce a 2D figure. The fourth dimension can be mapped to time to produce an animation.

Each polytwister has two tabs: a "rendered" tab where you can view a pre-made video of the animated polytwister with proper lighting, and an "interactive" tab which allows you to rotate the figure as well. You can download cross sections as meshes for use in your projects.

## How were these shapes made?

Using cylinders. Every polytwister cross section, and thus every frame of these animations, is the result of Boolean operations (intersection, difference, union) on scaled, rotated, and translated cylinders.

Blender's Python scripting capabilities were used to compute the meshes. The renders were also done in Blender.

## What are polytwisters?

Polytwisters are hard to explain, and some parts of their definition are currently unclear or conjectural. As of this writing, a paper is forthcoming that attempts to give precise definitions of what polytwisters are. The following explanation is intentionally informal.

While every two distinct great circles on the sphere must intersect at exactly two points, this is not necessarily true on the 3-sphere, which is the 4D analogue of the sphere. In fact, there are great circles on the 3-sphere that don't intersect with each other at all. Furthermore, it is possible to partition the 3-sphere into a set of mutually nonintersecting great circles that completely cover the 3-sphere.

Hopf fibration is a certain continuous bijection *h* from these great circles (also called fibers) to points of the ordinary sphere. Hopf fibration is a famous example of a nontrivial fiber bundle, and is often studied by mathematicians for its topological properties. However, its geometrical properties are interesting too. *h* is highly symmetrical and can be expressed concisely in terms of quaternions.

Bowers noticed that the inverse of *h*, mapping points on the sphere to fibers on the 3-sphere, can be used to transform a subset of convex polyhedra. Suppose we have a convex polyhedron whose faces are all tangent to an inscribed sphere. Every point of tangency can be mapped to a great circle on the 3-sphere. From each great circle we erect a *cycloplane*, which is a 4D analogue of an infinitely long cylinder. If we take the intersection of all resulting cycloplanes, we have a convex polytwister. Due to the symmetry of *h*, the convex polytwister's symmetry group is closely related to the original polyhedron's, but in a nontrivial way. Nonconvex polytwisters are produced by using arbitrary Boolean operations on cycloplanes.

Polytwisters are believed to have a structure analogous to polyhedra. The vertices of the polyhedron are mapped to *rings*, which are fibers plus a scaling about the origin. Edges become *strips*, which look like a strip of paper twisted 360 degrees with both ends attached (a Mobius strip with an extra half turn). Finally, faces become 3-dimensional *twisters*, which are polygonal rods also twisted 360 degrees with both ends connected. However, these elements are derived solely from visual inspection and have not yet been formally verified.
