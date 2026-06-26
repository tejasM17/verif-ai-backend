NAME_ROOTS = [
    "Nova", "Zen", "Apex", "Flux", "Core", "Pulse", "Echo", "Wave", "Spark", "Forge",
    "Lumen", "Arc", "Prime", "Quantum", "Nebula", "Stratus", "Cumulus", "Cirrus",
    "Cipher", "Vector", "Matrix", "Orbit", "Helix", "Prism", "Vertex", "Axiom",
    "Pixel", "Binary", "Logic", "Synth", "Mesh", "Node", "Link", "Grid", "Loop",
    "Beacon", "Cortex", "Synapse", "Axis", "Phase", "Signal", "Bridge", "Portal",
    "Nexus", "Apex", "Atlas", "Titan", "Vanguard", "Pinnacle", "Catalyst", "Lattice",
    "Helio", "Solaris", "Lunar", "Stellar", "Astra", "Cosmos", "Meridian", "Equinox",
    "Quanta", "Photon", "Plasma", "Halo", "Aurora", "Borealis", "Solstice", "Eclipse",
    "Vertex", "Ascend", "Empyrean", "Zenith", "Polaris", "Sirius", "Vega", "Orion",
    "Hydra", "Phoenix", "Griffin", "Sphinx", "Kraken", "Pegasus", "Chimera", "Dragon",
    "Wolf", "Falcon", "Raven", "Hawk", "Eagle", "Tiger", "Panther", "Lynx",
    "Cipher", "Shadow", "Phantom", "Specter", "Wraith", "Ghost", "Mirage", "Illusion",
    "Forge", "Anvil", "Crucible", "Foundry", "Smithy", "Mint", "Quarry", "Loom",
    "Spindle", "Gear", "Piston", "Lever", "Crank", "Wheel", "Spring", "Bearing",
    "Quill", "Ink", "Scroll", "Codex", "Atlas", "Compass", "Chrono", "Tempo",
    "Cadence", "Rhythm", "Harmony", "Melody", "Lyric", "Verse", "Stanza", "Crescendo",
    "Polaris", "Anchor", "Beacon", "Compass", "Harbor", "Port", "Haven", "Refuge",
    "Summit", "Ridge", "Peak", "Crest", "Bluff", "Canyon", "Valley", "Glen",
    "Delta", "Omega", "Sigma", "Alpha", "Beta", "Gamma", "Theta", "Lambda",
    "Rune", "Glyph", "Sigil", "Token", "Shard", "Prism", "Facet", "Crystal",
    "Glass", "Mirror", "Lens", "Scope", "Periscope", "Spyglass", "Telescope", "Microscope",
    "Cinder", "Ember", "Spark", "Flame", "Blaze", "Inferno", "Pyre", "Torch",
    "Tide", "Surf", "Reef", "Coral", "Pearl", "Shell", "Sandbar", "Lagoon",
    "Pine", "Oak", "Elm", "Maple", "Birch", "Cedar", "Willow", "Cypress",
    "Stone", "Granite", "Marble", "Slate", "Quartz", "Onyx", "Jade", "Obsidian",
    "Ruby", "Sapphire", "Emerald", "Topaz", "Amber", "Opal", "Diamond", "Garnet",
    "Iron", "Steel", "Copper", "Bronze", "Silver", "Gold", "Platinum", "Titanium",
]

SUFFIXES = [
    "Labs", "Systems", "Technologies", "Solutions", "Networks", "Cloud", "AI",
    "Analytics", "Dynamics", "Digital", "Works", "Hub", "Forge", "Studio",
    "Group", "Ventures", "Capital", "Partners", "Holdings", "Industries",
    "Software", "Data", "Robotics", "Mobility", "Health", "Bio", "Sciences",
    "Energy", "Power", "Logistics", "Trade", "Markets", "Bank", "Trust",
    "Securities", "Credit", "Loans", "Insurance", "Mutual", "Asset", "Research",
    "Foundation", "Institute", "Academy", "School", "Learning", "Education",
    "Media", "Press", "Publishing", "Broadcast", "Studio", "Productions",
    "Interactive", "Games", "Entertainment", "Studios", "Pictures", "Records",
    "Connect", "Mesh", "Grid", "Net", "Link", "Sync", "Stream", "Flow",
    "Bridge", "Path", "Route", "Way", "Channel", "Pipeline", "Express", "Cargo",
]

NAME_STYLES = [
    "{root}",
    "{root}{suffix}",
    "{root} {suffix}",
    "{root}.{root}",
    "{root}{root}",
    "{prefix} {root}",
    "{root} {postfix}",
]

PREFIXES = ["The", "New", "Next", "Modern", "Smart", "Hyper", "Meta", "Ultra", "Super", "Neo"]

POSTFIXES = ["Global", "Worldwide", "International", "Holdings", "Group", "Co", "Inc"]


def generate_name(rng, style_choices: list[str] | None = None, region_flavor: str | None = None) -> str:
    style = rng.choice(style_choices if style_choices else NAME_STYLES)
    root = rng.choice(NAME_ROOTS)
    suffix = rng.choice(SUFFIXES)
    prefix = rng.choice(PREFIXES)
    postfix = rng.choice(POSTFIXES)
    secondary = rng.choice(NAME_ROOTS)
    name = style.format(
        root=root, suffix=suffix, prefix=prefix, postfix=postfix, secondary=secondary,
    )
    if region_flavor:
        if rng.random() < 0.15:
            name = f"{name} {region_flavor}"
    return name


__all__ = ["generate_name", "NAME_ROOTS", "SUFFIXES"]
