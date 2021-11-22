Class {
	#name : #StateLeaksStencil,
	#superclass : #BrStencil,
	#instVars : [
		'method',
		'view'
	],
	#category : #CraftingToolsForUnderstandingSoftware
}

{ #category : #visualization }
StateLeaksStencil >> create [ 
	| path  allInvokedMethods methods entryMethodAttributes allAccessedAttributes nonInitializedAttributes |
path := OrderedCollection with: self method.
allInvokedMethods := Set new.

[ path isNotEmpty] whileTrue: [
	| m |
	m := path removeFirst.
	(m parentType container mooseName beginsWith: 'es::osoco::bbva') ifTrue: [
	allInvokedMethods add: m. 
	path addAll: (m invokedMethods select: [ :each |
		(allInvokedMethods includes: each) not ]).
		]
].
methods := allInvokedMethods asOrderedCollection.

entryMethodAttributes := 
	(self method query: #out with: FAMIXAccess) 
		opposites atScope: FAMIXAttribute.
		
allAccessedAttributes := Set new.
methods inject: allAccessedAttributes into: [ :attributes :aMethod |
	attributes addAll: ((aMethod query: #out with: FAMIXAccess) 
		opposites atScope: FAMIXAttribute).
	attributes].
	
nonInitializedAttributes := allAccessedAttributes select:[:attribute | 
	(attribute incomingAccesses select: [:access | 
		allInvokedMethods includes: access accessor]) allSatisfy: [ :x |
			x isWrite not ]			
].

		
view nodes 
	shape: [ :each |
		| element |
		element := BlElement new
			size: 15@15;
			geometry: BlCircleGeometry new;
			border: (BlBorder paint: (Color blue alpha: 0.4) width: 2).
		element background: (each accesses detect: [ :access | 
			nonInitializedAttributes includes: access variable ]
				ifFound: [ Color lightRed ] 
				ifNone: [Color lightGreen]); 
		yourself.
	];
	with: methods.

view nodes 
	shape: [ :each |
		BlElement new
			size: 9@9;
			geometry: (each hasClassScope 
				ifTrue: [BlPolygon vertices: { 0@5 . 5@0 . 10@5 . 5@10 }] 
				ifFalse: [ BlSquare new]);
			background: ((each incomingAccesses select: [:access | allInvokedMethods includes: access accessor ]) 
				detect: [:anAccess | anAccess isWrite ] 
				ifFound: [ Color lightGreen] 
				ifNone: [ Color lightRed])
	];
	with: allAccessedAttributes.
	
view edges 
	fromNearestTightCircle;
	toNearestTightCircle;
	shape: [:x | 
		BlLineElement new
			border: (BlBorder paint: (Color blue alpha: 0.4) width: 2);
			toHead: (BlArrowheadSimpleArrow new
				arrowLengthFraction: 5;
				arrowNoseAngle: 60;
				border: (BlBorder paint: (Color blue alpha: 0.4) width: 1))
	];
	connect: methods fromAll: [ :each |  each invokingMethods ].
	
view edges 
	fromNearestTightCircle;
	toNearestTightCircle;
	shape: [:x | 
		BlLineElement new
			border: (BlBorder paint: (Color lightGray) width: 2)
	];
	connect: allAccessedAttributes fromAll: [ :each | 
		each incomingAccesses 
			select: [:anAccess | anAccess isWrite not ] thenCollect: [ :a | a accessor ]
	].
		
view edges 
	fromNearestTightCircle;
	toNearestTightCircle;
	shape: [:x | 
		BlLineElement new
			border: (BlBorder paint: (Color lightGreen) width: 3)
	];
	connect: allAccessedAttributes fromAll: [ :each | 
		each incomingAccesses 
			select: [:anAccess | anAccess isWrite ] thenCollect: [ :a | a accessor ] ].

view layout tree 
	nodeDistance: 5;
	levelDistance: 20.

	
^ view

]

{ #category : #accessing }
StateLeaksStencil >> method [
	^ method
]

{ #category : #accessing }
StateLeaksStencil >> method: aMethod [
	method := aMethod
]

{ #category : #accessing }
StateLeaksStencil >> view: aView [
	view := aView
]
