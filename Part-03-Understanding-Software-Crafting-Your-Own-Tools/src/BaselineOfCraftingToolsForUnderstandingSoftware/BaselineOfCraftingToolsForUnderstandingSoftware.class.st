Class {
	#name : #BaselineOfCraftingToolsForUnderstandingSoftware,
	#superclass : #Object,
	#category : #BaselineOfCraftingToolsForUnderstandingSoftware
}

{ #category : #accessing }
BaselineOfCraftingToolsForUnderstandingSoftware >> baseline: spec [
	<baseline>
	spec
		for: #common do: [
			spec
				package: 'CraftingToolsForUnderstandingSoftware' ]
]

{ #category : #accessing }
BaselineOfCraftingToolsForUnderstandingSoftware >> loadLepiter [
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
