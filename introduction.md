# Polytwisters

## What is this?

This is a Web app that presents *polytwisters*, a class of strange curved shapes with four spatial dimensions discovered by amateur mathematician Jonathan Bowers. Mathematically, polytwisters are the result of combining Hopf fibration with polyhedra. As 4D objects can't be completely perceived in our world, this app uses 3D cross sections of polytwisters, just as every 3D object can be sliced by a plane to produce a 2D figure. The fourth dimension can be mapped to time to produce an animation.

Each polytwister has two tabs: a "rendered" tab where you can view a pre-made video of the animated polytwister with proper lighting, and an "interactive" tab which allows you to rotate the figure as well. You can download cross sections as meshes for use in your projects.

## What are polytwisters?

Polytwisters are hard to explain, and some parts of their definition are currently unclear or conjectural. As of this writing, a paper is forthcoming that attempts to give precise definitions of what polytwisters are. The following is a lay explanation.

The 4D analogue of the sphere is called the 3-sphere (it's embedded in 4D space, but it's so called because it is really a three-dimensional manifold). Like the ordinary sphere, you can draw a great circle on the 3-sphere that has the maximum possible radius and is centered on the origin, like the equator.

While every two distinct great circles on the sphere must intersect at exactly two points, this is not necessarily true on the 3-sphere. There are great circles on the 3-sphere that don't intersect with each other at all. Furthermore, it is possible to partition the 3-sphere into a set of mutually nonintersecting great circles that completely cover the 3-sphere.

Hopf fibration is a certain continuous many-to-one mapping *h* from these great circles, known as Hopf fibers, to points of the ordinary sphere. Hopf fibration is a famous example of a nontrivial fiber bundle, and is often studied by mathematicians for its topological properties. However, its geometrical properties are interesting too. *h* is highly symmetrical and can be expressed concisely in terms of quaternions (4D analogue of the complex numbers).

Bowers, the discoverer of polytwisters, describes them as the "lovechild" of Hopf fibration and polyhedra. If you have a polyhedron inscribed in a sphere, you can invert *h* to map the points on a sphere to a set of Hopf fibers. To turn these fibers into a solid 4D shape, we can for example take the convex hull. This produces something called a "soft polytwister." The shapes you see are "hard polytwisters;" the exact way they're constructed is pretty technical, but the gist is that they're Boolean operations on 4D cylinders erected from the circles.

Given a 4D solid shape, we can slice it using a 3-space to get a 3D cross section. By mapping the fourth dimension to time, polytwisters can be realized as smooth animations of 3D shapes. Sadly, cross sections have to be taken at a somewhat arbitrary angle and we can't really see the full symmetry that a 4D person would. Such are the pains of working with higher-dimensional geometry: beauty we can't perceive without compromise.

## How were these shapes made?

Using cylinders. Every polytwister cross section, and thus every frame of these animations, is the result of Boolean operations on transformed cylinders.

Blender's Python scripting capabilities were used to compute the meshes, although they could likely be computed in any mesh processing environment that supports Boolean operations. The raw data is open.
