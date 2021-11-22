Extension { #name : #FAMIXMethod }

{ #category : #'*CraftingToolsForUnderstandingSoftware' }
FAMIXMethod >> gtStateLeakFor: aView [
	<gtView>
	^ aView mondrian
		title: 'State Leaks';
		priority: 6;
		painting: [ :view | 
			(StateLeaksStencil new 
				view: view; 
				method: self;
				yourself) asElement
		]
]
