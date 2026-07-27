# FreeCAD Addon Academy source routing

Use this index to retrieve only the sources needed for the question. The
published root is <https://freecad.github.io/Addon-Academy/> and the source
repository is <https://github.com/FreeCAD/Addon-Academy>.

The repository default branch was `main` and its observed head was
`833bb4852af825e1826b83d6b75872d18b433486` on 2026-07-27. Treat this as
retrieval evidence, not a pinned project dependency. Recheck the head whenever
revision-sensitive guidance is requested.

## Route by question

| Question | Published route | Source path |
| --- | --- | --- |
| Addon kind: workbench, macro, preference pack or bundle | `/Topics/Types/` | `Source/Topics/Types/` |
| Modern namespaced versus legacy layout; `package.xml` | `/Topics/Structuring/` | `Source/Topics/Structuring/` |
| Scaffold or template choice | `/Guides/Creating/` | `Source/Guides/Creating/` |
| Workbench registration | `/Guides/Code/Workbench/` | `Source/Guides/Code/Workbench/` |
| GUI command registration | `/Guides/Code/Commands/` | `Source/Guides/Code/Commands/` |
| Qt/PySide UI | `/Guides/Code/Qt/` | `Source/Guides/Code/Qt/` |
| Preferences | `/Guides/Code/Preferences/` | `Source/Guides/Code/Preferences/` |
| Custom document objects and ViewProviders | `/Guides/Code/Document-Objects/` | `Source/Guides/Code/Document-Objects/` |
| Icons and resources | `/Guides/Code/Icons/` | `Source/Guides/Code/Icons/` |
| Translation | `/Guides/Code/Translations/` | `Source/Guides/Code/Translations/` |
| Logging and console behaviour | `/Guides/Code/Logging/` | `Source/Guides/Code/Logging/` |
| Local installation, debugging or testing | `/Guides/Developing/` | `Source/Guides/Developing/` |
| Dependency allow-list or vendoring | `/Topics/Dependencies/` | `Source/Topics/Dependencies/` |
| Code/assets licences and SPDX | `/Topics/Licensing/` | `Source/Topics/Licensing/` |
| Portable, referenced or indexed publication | `/Guides/Publishing/` | `Source/Guides/Publishing/` |
| Manifest polish, overview and screenshots | `/Guides/Polish/` | `Source/Guides/Polish/` |
| Addon Index requirements and quality criteria | `/Topics/Addon-Index/` | `Source/Topics/Addon-Index/` |
| FreeCAD compatibility, migrations, updates or handoff | `/Guides/Maintaining/` | `Source/Guides/Maintaining/` |
| Academy/FreeCAD terms | `/Topics/Glossary/` | `Source/Topics/Glossary/` |

Start at a section index when the exact child path is uncertain. Follow its
links rather than guessing a filename.

## Demos

Use demos after reading the owning guide or topic. They demonstrate mechanics;
they do not establish TrackTemplate architecture or production readiness.

| Demonstration | Published route | Source path |
| --- | --- | --- |
| Extend an existing toolbar | `/Demos/Extend-Toolbar/` | `Source/Demos/Extend-Toolbar/` |
| Minimal workbench | `/Demos/Minimal-Workbench/` | `Source/Demos/Minimal-Workbench/` |
| Parametric feature and ViewProvider | `/Demos/Parametric-Feature/` | `Source/Demos/Parametric-Feature/` |
| Preferences page | `/Demos/Preferences-Page/` | `Source/Demos/Preferences-Page/` |
| Standalone macro | `/Demos/Macro/` | `Source/Demos/Macro/` |

## Source hierarchy

Use this order unless the question requires a lower-level authority:

1. Academy published guide/topic for current Addon guidance.
2. Matching Academy GitHub source for revision, exact snippets and notices.
3. Official FreeCAD API/source for runtime behavior.
4. Official Addon Template or Addon Index for current packaging/acceptance
   mechanics.
5. TrackTemplate canonical documents for project requirements and decisions.

Community forum posts, third-party addons and search snippets may locate
evidence but do not replace a first-party source.

## Licensing boundary

The repository identifies `LICENSE-CODE` as GNU LGPL 2.1 and `LICENSE-DOCS` as
CC BY-SA 4.0. The Academy landing source says its demos are CC0. Inspect the
specific file and local notice before copying because prose, Academy
infrastructure and demo code do not share one blanket licence. Prefer a short
summary and link; record attribution and adaptation obligations for any
retained extract.
