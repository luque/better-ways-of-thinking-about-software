Class {
	#name : #BaselineOfCraftingToolsForUnderstandingSoftware,
	#superclass : #BaselineOf,
	#category : #BaselineOfCraftingToolsForUnderstandingSoftware
}

{ #category : #accessing }
BaselineOfCraftingToolsForUnderstandingSoftware class >> loadLepiter [
	| currentProperties |
	currentProperties := LeDatabasesRegistry defaultLogicalDatabase properties.
	currentProperties
		addRegisteredDirectory: FileLocator imageDirectory
			/ 'pharo-local'
			/ 'iceberg'
			/ 'osoco'
			/ 'better-ways-of-thinking-about-software'
			/ 'Part-03-Understanding-Software-Crafting-Your-Own-Tools'
			/ 'lepiter'.
	
	LeDatabasesRegistry default defaultLogicalDatabase reload.
]

{ #category : #accessing }
BaselineOfCraftingToolsForUnderstandingSoftware >> baseline: spec [
	<baseline>
	spec
		for: #common do: [
			spec
				package: 'CraftingToolsForUnderstandingSoftware' ]
]
