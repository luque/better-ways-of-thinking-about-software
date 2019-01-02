			var shift,
				guides = true,
				geartext = true,
				grid = true,
				AM = 180/Math.PI,
				font = ["ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-/=*;:,.<>", "0204284442324335464738181215080307480525452224683316263634174130100106373120004014232713", "4ABCDE/BD 4AFGDHIJKLM/NH/OL 4GFMPQLKJ 4AFGJKO/LM 4EAOR/ST 4AOR/ST 4HUEMPQLR 4ER/US/OA 2VA/ML/CO 4RGFMP 4ENR/AO/NS 4EAO 4ERWOA 4REOA 4UGFMPQLKJU 4SHIJKOA 4DVMPQLKJD 4ENHIJKOA/NS 4JKLQGFMP 4RO/CV 4RGFMPO 6XFO 6XEHVO 4RA/EO 4RTO/TV 4EARO 4YVMPSZaHYE 4OBabUGFVBA 4EMPSZI 4EDVMPSZaDR 4FMPSZbUcB 4MdCKJ/HS 4EMPSZbUefgh 4BabUE/AO 0Ai/QO 3Kj/bklgh 4EWI/AO/WB 1MPO 4Ai/SZTbUE/WT 4Ai/BabUE 4GFMPSZbUG 4mi/SZbUGFA 4nI/EMPSZbU 4Ai/BabU 4IZSocGFA 4GFpC/Ii 4IE/DVMPi 4IVi 4IFaMi 4IA/Ei 4Igm/Vi 4EAIi 3YVMPQLCjY 2QLM/VA 4EABNHIJKLQ 4QLKJIHDGFMP/TH 4DBKF 4ROibUGFMP 4SHDGFMPiCK 4ORV 4NBPMFGDHNiQLKJIH 4UNiQLKJDVM 4pq/US 4US 4RA 4Ii/DB 4US/pq/JP/GQ 1ZN/oMh 1ZN/or 1rMh 0PA 3KSF 3OHA"],
				baserot = 0,
				rot = baserot,				// global base rotation
				RPM = 4,
				realRPM = 4,
				rota = 0,
        animation = true,
        loop = true,
				gears = [],
				selectedgear = -1,
				defaultgear = {	ID: -1,	N: 9, D: 1.5, P: 6, PA: 20, rot: rot, gearangle: 0, jointangle: -60	},
				has3d,
				theme = 1;

			function fixInput( v, setFN, def, min, max ) {
				if( isNaN( v ) ) v = def;
				if( min != undefined && v<min ) v=min;
				else if( max != undefined && v>max ) v=max;
				setFN( v );
				return v;
			}
			function getNfix() { return fixInput( Number( $("#N").val() ), setN, gears[selectedgear].N, 4, 0 ); }
			function getN() { //return Number( $("#N").val() );
					return 8;
			}
			function setN( v ) { $("#N").val( v ); }
			function getDfix() { return fixInput( Number( $("#D").val() ), setD, gears[selectedgear].D, 0.1 ); }
function getD() { //return Number( $("#D").val() );
		return 2;
}
			function setD( v ) { $("#D").val( v ); }
			function getPfix() { return fixInput( Number( $("#P").val() ), setP, gears[selectedgear].P, 1, 0 ); }
			function getP() { return Number( $("#P").val() ); }
			function setP( v ) { $("#P").val( v ); }
			function getPAfix() { return fixInput( Number( $("#PA").val() ), setPA, gears[selectedgear].PA, 12, 35 ); }
			function getPA() { return Number( $("#PA").val() ); }
			function setPA( v ) { $("#PA").val( v ); }
			function getRPMfix() { return fixInput( Number( $("#RPM").val() ), setRPM, RPM, -360, 360 ); }
			function getRPM() { //return Number( $("#RPM").val() );
					return 6;
			}
			function setRPM( v ) { $("#RPM").val( v ); }
			function getscalefix() { return fixInput( Number( $("#scale").val() ), setscale, 100, 25, 400 ); }
			function getscale() {
					//return Number( $("#scale").val() );
					return 100;}
			function setscale( v ) { $("#scale").val( v ); }
			function getPGfix() { return fixInput( Number( $("#PG").val() ), setPG, gears[selectedgear].parentID, -1 ); }
			function getPG() { return Number( $("#PG").val() ); }
			function setPG( v ) { $("#PG").val( v ); }
			function getCAXLE() { return !!$("#CAXLE:checked").val(); }
			function setCAXLE( v ) { $("#CAXLE").prop("checked", v==true ); }
			function getgrid() { return !!$("#grid:checked").val(); }
			function setgrid( v ) { $("#grid").prop("checked", v==true ); }
			function getguides() { return !!$("#guides:checked").val(); }
			function setguides( v ) { $("#guides").prop("checked", v==true ); }
			function getlabels() { return !!$("#labels:checked").val(); }
			function setlabels( v ) { $("#labels").prop("checked", v==true ); }
			function getCAfix() { return fixInput( Number( $("#CA").val() ), setCA, gears[selectedgear].jointangle ); }
			function getCA() { return Number( $("#CA").val() ); }
			function setCA( v ) { $("#CA").val( v ); }

			// --------------------------------------------------------------------------------------------------

			function Nadd( a ) {
				setN( getN()+a );
				Nchange();
			}
			function PAadd( a ) {
				setPA( getPA()+a );
				PAchange();
			}
			function Aadd( a ) {
				setCA( getCA()+a );
				CAchange();
			}
			function scalem( m ) {
				setscale( getscale()*m );
				scaleChange();
			}

			function Nchange() {
				if( shift ) {
					setP( getNfix()/getD() );
					updatePitches();
				} else {
					setD( getNfix()/getP() );
					updateGears();
				}
			}
			function Dchange() {
				if( shift ) {
					setP( getN()/getDfix() );
					updatePitches();
				} else {
					setN( Math.floor( getDfix()*getP() ) );
					Nchange();
				}
			}
			function Pchange() {
				setD( getN()/getPfix() );
				updatePitches();
			}
			function PAchange() {
				getPAfix();
				updatePitches();
			}
				function calcP() {
					setP( getN()/getD() );
				}

			function RPMchange() {
				RPM = getRPMfix();
				if( shift ) {
					RPM = RPM/gears[selectedgear].totalratio;
					setRPM( RPM );
				}
				updateListItemText( 0 );
				updateHash();
			}
			function scaleChange() {
				getscalefix();
				renderAllGears();
				updateHash();
			}
			function CAchange() {
				gears[selectedgear].jointangle = getCAfix();
				positionGears( selectedgear );
				rotateGears( selectedgear );
				updateHash();
				maxSize();
			}
			function PGchange() {
				var ID = selectedgear,
						gear = gears[ID],
					pID = gear.parentID,
					PG = getPGfix();
				if( PG>=0 && !isChildOf( PG, ID ) && PG != pID && PG<gears.length) {
					var parentChilds = gears[pID].childIDs;
					parentChilds.splice( parentChilds.lastIndexOf( ID ), 1);
					gear.parentID = PG;
					gears[gear.parentID].childIDs.push( ID );
					updateJoint();
				} else setPG( pID );
			}

			function CAXLEchange() {
				var ID = selectedgear,
					gear = gears[ID];

				if( gear.parentID<0 ) {
					setCAXLE( true );
					return;
				}
				updateJoint();
			}
			function updateJoint() {
				var ID = selectedgear,
					gear = gears[ID],
					pP = gears[gear.parentID].P,
					pPA = gears[gear.parentID].PA;
				if( !(gear.axlejoint = getCAXLE()) && ( pP != getP() || pPA != getPA() ) ) {
					setD(getN()/pP);
					setP(pP);
					setPA(pPA);
					updatePitches();
				} else {
					positionGears( ID );
					rotateGears( ID );
					updateListItemText( ID );
					updateHash();
				}
			}

			function displaychange() {
				if( grid != (grid = getgrid()) ) makeGrid();
				guides = getguides();
				setGuidesClass();
				geartext = getlabels();
				setLabelsClass()

				writeCookies();
			}
			function setGuidesClass() {
				if( getguides() ) $("#screen").removeClass("noguides");
				else $("#cover-gears").addClass("noguides");
			}
			function setLabelsClass() {
				if( getlabels() ) $("#cover-gears").removeClass("nolabels");
				else $("#cover-gears").addClass("nolabels");
			}
			// --------------------------------------------------------------------------------------------------
      function createGear( N, D, P, PA, ID, text ) {
				var sc = getscale(),
					A = 1/P,
					B = 1.157/P,
					OD = (N + 2)/P,
					RD = (N - 2.3)/P,
					BC = D*Math.cos(PA*(Math.PI/180)),
					CP = Math.PI/P,
					rmin = RD/2,
					rmax = OD/2,
					rbase = BC/2,
					pts = [],
					ac = 0,
					aca = 0,
					w = Math.ceil( OD/2*sc )*2,
					h = w,

					addpts = function( p ) { pts.push( p );	},
					pt = function( r, a ) { return { r: r, a: a }; },

					out = '<?xml version="1.0" encoding="utf-8"?><!-- Generator: Iparigrafika Gear Generator by Abel Vincze http://geargenerator.com/ --><svg version="1.2" class="svggear" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="'+w+'px" height="'+h+'px" viewBox="'+(-w/2)+' '+(-h/2)+' '+w+' '+h+'" overflow="scroll" xml:space="preserve">';

				// calc
				addpts( pt( rmin, 0 ) );			//first point

				for( var i=1, pn=0, step=1, first = true; i<100; i+=step ) {
					// get a point...
					var bpl = polarToLinear( pt( rbase, -i ) ),			//base point linear
						len = ((rbase*Math.PI*2)/360)*i,				//length
						opl = polarToLinear( pt( len, -i+90 ) ),		//add line
						np = linearToPolar( { x: bpl.x+opl.x, y: bpl.y+opl.y } );

					if( np.r>= rmin ) {
						//console.log( np.a );
						if( first ) {
							first = false;
							step=(2/N)*10;
							//console.log("first point at "+i );
						}
						if( np.r<D/2 ) {
							ac = np.a;
							aca = i;
						}
						pn++;
						if( np.r> rmax ) {
							np.r = rmax;
							addpts( np );
							break;
						}
						addpts( np );
					}
				}
				// tukrozes
				var fa = 360/N,						// final a
					ma = fa/2 + 2*ac,				// mirror a
					fpa = (fa-ma)>0?0:-(fa-ma)/2,	// first point a
					m=pts.length;
				pts[0] = pt( rmin, fpa );			// fix first point a
				while( pts[m-1].a>ma/2 ) {
					pts.splice(m-1,1);
					m--;
					pn--;
				}

				for( var i=pn; i>=0; i-- ) {
					var bp = pts[i],
						na = ma-bp.a;
					addpts( pt( bp.r, na ) );
				}
				// repeat
				for( var i=1,m=pts.length; i<N; i++ ) {
					for( var p=0; p<m; p++ ) {
						var bp = pts[p],
							na = bp.a+fa*i;
						addpts( pt( bp.r, na ) );
					}
				}
				// print points
				out += '<polygon id="gearpoly'+ID+'" data-id="'+ID+'" class="gear" fill="#ddd" stroke="#444" stroke-width="1" stroke-miterlimit="10" points="';
				for( var i=0; i<pts.length; i++ ) {
					var point = polarToLinear( pts[i] );
					out += fix6(point.x*sc)+','+fix6(point.y*sc)+' ';
				}
				out += '"/>';

				// center cross
				out += '<g class="guides"><polyline fill="none" stroke="#444" stroke-width="0.5" stroke-miterlimit="10" points="';
				out += '10,0 -10,0"/>';
				out += '<polyline fill="none" stroke="#444" stroke-width="0.5" stroke-miterlimit="10" points="';
				out += '0,10 0,-10"/></g>';
				// first tooth marker
				var zpr = 1.57/P*sc/4;
					zp = polarToLinear( pt( D/2, ma/2 ) );
				out += '<circle fill="#c00" class="firstmarker" stroke="none" stroke-miterlimit="10" cx="'+fix6(zp.x*sc)+'" cy="'+fix6(zp.y*sc)+'" r="'+fix6(zpr)+'"/>';

				// text on wheel
					//        	var tdata = makeText("*"+ID+" N="+N+" Pitch D="+fix2(D)+" P="+fix2(P)+" PA="+fix2(PA), 2),
					var tdata = makeText(text, 2),
					textH = (RD/2)/7/6,	// betu magassaga (/6 a pixelmagassag miatt)
					textH = textH>0.03?0.03:textH,
					textB = (RD/2)-textH*10,	// alapvonal 75%-nal
					plotAngle = 180/((textB*Math.PI)/textH);


				out += '<g class="geartext">'+renderSVGPrecisionPolarText( tdata, textB, textH, plotAngle, sc )+'</g>';
				// guides
				out += '<g class="guides gearguides" opacity="0.2">';
				out += '<circle class="pitch" fill="none" stroke="#f00" stroke-miterlimit="10" cx="0" cy="0" r="'+fix2((D/2)*sc)+'"/>'; // pitch circle
				//out += '<circle class="root" fill="none" stroke="#ccc" stroke-miterlimit="10" cx="0" cy="0" r="'+fix2((RD/2)*sc)+'"/>'; // Root circle
				out += '<circle class="outer" fill="none" stroke="#ccc" stroke-miterlimit="10" stroke-dasharray="2,2" cx="0" cy="0" r="'+fix2((OD/2)*sc)+'"/>'; // Outer circle
				out += '<circle class="base" fill="none" stroke="#00f" stroke-miterlimit="10" stroke-dasharray="2,2" cx="0" cy="0" r="'+fix2((BC/2)*sc)+'"/>'; // Base circle
				out += '</g>';

				out += '</svg>';


				return { svg: out, gearangle: fa, baseangle: ac, Rsc: D*sc/2, w: w, h: h };
			}
			function linearToPolar( c ) {
				var x = c.x, y = c.y, r, a;
				//var AM = 180/Math.PI;
				r = Math.sqrt( x*x + y*y );
				a = Math.asin( y/r )*AM;
				if( x<0 ) a = 180-a;
				a = (a+360)%360;
				return { r: r, a: a }
			}
			function polarToLinear( p ) {
				var r = p.r, a = p.a, x, y;
				//var AM = 180/Math.PI;
				a = ((a+360)%360)/AM;

				x = Math.cos( a )*r;
				y = -Math.sin( a )*r;

				return { x: x, y: y }
			}

			function fix2( v ) {
				return Math.round( 100*v )/100;
			}
			function fix6( v ) {
				return Math.round( 10000*v )/10000;
			}

			function createSVGgrid( sc ) {
				/*var cl = $("body").attr("class"),
					col;

				if(cl=="col0") col = "#888";
				if(cl=="col1") col = "#fff";
				if(cl=="col2") col = "#888";*/


				var col = ["#888","#fff","#888"][theme],
					subd = 10,
					weight = 1,
					scdot = sc+0.5;
					out = '<svg version="1.2" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="'+sc+'px" height="'+sc+'px" viewBox="0 0 '+sc+' '+sc+'" xml:space="preserve">';	//+out+'</svg>';

				out += '<g class="grid" stroke="'+col+'" opacity="0.2">'
				out += '<polyline fill="none" stroke-width="'+weight+'" stroke-linecap="square" stroke-miterlimit="2"  points="';
				out += '0.5 '+scdot+' 0.5 0.5 '+scdot+' 0.5"></polyline>';

				for( var i=1; i<10; i++ ) {
					var pos = (sc/10)*i+0.5;
					out += '<polyline fill="none" stroke-width="'+(weight/2)+'" stroke-linecap="square" stroke-miterlimit="2"  points="0.5 '+pos+' '+scdot+' '+pos+'"></polyline>';
					out += '<polyline fill="none" stroke-width="'+(weight/2)+'" stroke-linecap="square" stroke-miterlimit="2"  points="'+pos+' 0.5 '+pos+' '+scdot+'"></polyline>';

				}

				out += '</g></svg>';
				return out;
			}
			function makeGrid() {
				if( grid ) {
					var svg = createSVGgrid( getscale() ),
						b64 = 'data:image/svg+xml;base64,' + window.btoa(svg),
						url = 'url("' + b64 + '")';
				} else {
					var url = "none";
				}
				$('#cover-gears').css('backgroundImage', url);

			}
			// -------------- FONT
			function getchardata( chr ) {
				var i=font[0].lastIndexOf( chr ),
					data=[];
				if( i>-1 ) {
					var chdata = font[2].split(" ")[i],
						l = 0;
					data[0] = Number(chdata.substr(0,1));
					for( var p=0,pi; p<chdata.length; p++ ) {
						pi = getindex( chdata.charCodeAt(p) );
						if( pi<0 ) data[++l] = [];
						else data[l].push( font[1].substr( pi ,2 ) );
					}
				} else data[0]=chr==" "?3:-1;
				return data;
			}
			function getindex( code ) {
				code-=65;
				code>25&&(code-=6);
				return code*2;
			}

			function makeText( txt, chs ) {
				var width,
					pos = 0,
					  data = [0];
        txt = txt || "";

				chs = chs==undefined?1: chs;
				for( var i=0, cdata; i<txt.length; i++ ) {
					cdata = getchardata( txt.substr( i, 1 ) );
					if( cdata[0]>=0 ) {
						for(var l=1; l<cdata.length; l++ ) {
							for( var p=0, pt, line=[]; p<cdata[l].length; p++ ) {
								pt = cdata[l][p].split("");
								line.push( { x: Number(pt[0])+pos, y: Number(pt[1]) } );
							}
							data.push( line );
						}
						pos += chs+cdata[0];
					}
				}
				if( pos>0 ) data[0] = pos-1;
				return data;
			}
			function renderSVGLinearText( tdata, textB, pixH, weight ) {
				var out = '<g class="text">',
					add = weight/2;
				if( add<0.5 ) add = 0.5;

				for( var i=1; i<tdata.length; i++ ) {
					out += '<polyline fill="none" stroke="#444" stroke-width="'+weight+'" stroke-linecap="square" stroke-miterlimit="2"  points="';
					for( var p=0; p<tdata[i].length; p++ ) {
						out += (tdata[i][p].x*pixH+add) + " " + (textB-tdata[i][p].y*pixH+add) + " ";
					}
					out += '"/>';
				}
				out += "</g>";
				return out;
			}
			function renderSVGPolarText( tdata, textB, pixH, plotAngle, sc ) {

				var angularLength = tdata[0]*plotAngle,		// angular length of the text
					ba = angularLength/2,					// base angle
					out = '<g class="text">';

				for( var i=1; i<tdata.length; i++ ) {
					out += '<polyline fill="none" stroke="#444" stroke-width="0.5" stroke-linecap="square" stroke-miterlimit="1"  points="';
					for( var p=0, a, r, dot; p<tdata[i].length; p++ ) {
						a = -tdata[i][p].x * plotAngle + ba;
						r = (tdata[i][p].y-5) * pixH + textB;
						dot = polarToLinear( { r: r, a: a } );
						out += dot.x*sc + " " + dot.y*sc + " ";
					}
					out += '"/>';
				}
				out += "</g>";
				return out;
			}
			function renderSVGPrecisionPolarText( tdata, textB, pixH, plotAngle, sc ) {

				var angularLength = tdata[0]*plotAngle,		// angular length of the text
					ba = angularLength/2,					// base angle
					out = '<g class="text">';

				for( var i=1; i<tdata.length; i++ ) {
					out += '<polyline fill="none" stroke="#444" stroke-width="0.5" stroke-linecap="square" stroke-miterlimit="1"  points="';
					for( var p=0, a, r, dot, dx, inc, lx, ly, x, y, mp=tdata[i].length; p<mp; p++ ) {

						x = tdata[i][p].x;
						y = tdata[i][p].y;
						if( p==0 ) {
							lx = x;
							ly = y
							a = -lx * plotAngle + ba;
							r = (ly-5) * pixH + textB;
							dot = polarToLinear( { r: r, a: a } );
							out += fix2(dot.x*sc) + " " +fix2(dot.y*sc) + " ";
						} else {
							dx = Math.abs( x-lx );
							if( dx==0 ) {
								dx=1;
							}
							ix = ( x-lx )/dx;
							iy = ( y-ly )/dx;
							for( var s=1, X, Y; s<=dx; s++ ) {
								Y = ly + iy*s;
								X = lx + ix*s;
								a = -X * plotAngle + ba;
								r = (Y-5) * pixH + textB;
								dot = polarToLinear( { r: r, a: a } );
								out += fix2(dot.x*sc) + " " + fix2(dot.y*sc) + " ";
							}
							lx = x;
							ly = y;
						}
					}
					out += '"/>';
				}
				out += "</g>";
				return out;
			}

			function replaceWithSVGText( selection, upperCase, pixH, weight, chs  ) {
				pixH = pixH || 1;
				chs = chs==undefined? 2: chs;
				weight = weight || 1;

				var txt = selection.html();

				if( upperCase ) txt = txt.toUpperCase();

				var tdata = makeText( txt, chs ),
					w = tdata[0]*pixH+weight,
					h = pixH*8+weight,
					out = renderSVGLinearText( tdata, pixH*8, pixH, weight );

				out = '<svg version="1.2" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="'+w+'px" height="'+h+'px" viewBox="0 0 '+w+' '+h+'" xml:space="preserve">'+out+'</svg>';

				selection.html( out );
			}
			// --------------------------------------------------------------------------------------------------

			function addNewGear() {
				if( selectedgear<0 ) return;
				var gear = gears[selectedgear],
					P = gear.P,
					N = 13,
					D = N/P,
					PA = gear.PA;

				addGear( gear, false, N, D, P, PA );
			}
			function addGear( parentgear, axlejoint, N, D, P, PA, A ) {
				parentgear = parentgear || defaultgear;
				axlejoint = axlejoint || false;
				N = N || parentgear.N;
				D = D || parentgear.D;
				P = P || parentgear.P;
				PA = PA || parentgear.PA;
				A = A==undefined? parentgear.jointangle: A;

				var ID = addGearData( parentgear.ID, axlejoint, N, D, P, PA, A ).ID;
				addGearDataProcess( ID );
				updateGearDOM( ID );
				positionGears( ID );
				rotateGears( ID );
				selectGear( ID );
				updateHash();
				setListItemText( ID );
				maxSize();
				return gears[ID];
			}
      function addGearData( parentgearID, axlejoint, N, D, P, PA, A, text ) {
				var ID = gears.length,
				  thegear = createGear( N, D, P, PA, ID, text ),
					newgear = {
						ID:			ID,
						parentID:	parentgearID,
						axlejoint:	axlejoint,

						N:			N,
						D:			D,
						P: 			P,
						PA:			PA,
						// ez az uj fogaskerekbol adodik
						rot:		0,		// ezt nem igy persze
						gearangle:	thegear.gearangle,

						ratio:		1,
						totalratio: 1,

						jointangle:	A,			// default, hogy alatta...
						baseangle:	thegear.baseangle,
					//	geardata:	createGear( N,D,P ),

						Rsc:		thegear.Rsc,

						svg:		thegear.svg,
						svgwidth:	thegear.w,		// fogaskerek svg merete.
						svgheight:	thegear.h,
						svgoffsetx:	-thegear.w/2,		// svg offset a kozeppont pozicionalasahoz
						svgoffsety:	-thegear.h/2,
						offsetx:	0,
						offsety:	0,
						x:			0,			// aktualis pozicio, ezt ki kell szamolni a csatlakozas szogebol, tavolsagabol.
						y:			0,

						childIDs:	[]
					};
				gears[ID] = newgear;
				return gears[ID];
			}
			function addGearDataProcess( ID ) {
				var newgear = gears[ID],
					parentID = newgear.parentID,
					parentgear = (newgear.parentID<0)? defaultgear: gears[newgear.parentID];

				if( parentgear.ID >= 0 ) {
					gears[parentgear.ID].childIDs.push( ID );
				}

				// add gear to DOM
				$("#cover-gears").append( '<div id="gearcontainer'+ID+'" class="svg">'+newgear.svg+'</div>' );
				//$("#gearselector").append( '<li id="gearlistitem'+ID+'" data-id="'+ID+'" class="listitem"></li>' );
				//$("#gearlistitem"+ID).bind( "click", selectionClick );
				setGearEvents( ID );
				setListItemText( ID );
				return gears[ID];

			}
			function selectionClick() {
				var ID = Number($(this).attr("data-id"));
				if( ID == undefined ) return false;
				selectGear( ID );
				updateHash();
			}

			function removeGear() {

				//console.log(" childs: "+getTotalChildNumber( ID ));

				var ID = selectedgear,
					newgears = [],
					oldIDs = [],
					chg = getTotalChildNumber( ID );

				if( chg>0 ) {
						if (!confirm("This gear have "+chg+" child gear"+(chg>1?"s":"")+".\nChild gears will be also removed!")) return;
				}

				selectedgear = removeAllGears( ID );
				if( selectedgear<0 ) selectedgear = 0;

				//console.log( gears );

				// delete gear
				for( var i=0, newID=0; i<gears.length; i++ ) {
					if( gears[i] ) {

						newgears[newID] = gears[i];
						oldIDs[newID++] = i;


					}
				}

				gears = newgears;
				for( var i=0; i<gears.length; i++ ) {
					changeID( oldIDs[i], i );
					$("#gearlistitem"+oldIDs[i]).attr("id","gearlistitem"+i).attr("data-id", i );
					$("#gearcontainer"+oldIDs[i]).attr("id","gearcontainer"+i);
					$("#gearpoly"+oldIDs[i]).attr("id","gearpoly"+i).attr("data-id", i );
					if( selectedgear == oldIDs[i] ) selectedgear = i;
				}

				selectGear( selectedgear );
				renderAllGears();
				updateHash();
				updateListItemText(0);
				maxSize();
			}
			function removeAllGears( ID ) {

				var	gear = gears[ID],
					pi = gear.parentID,
					chs = gear.childIDs.slice();

				for( var i=0; i<chs.length; i++ ) {
					removeAllGears( chs[i] );
				}
				// remove this ID from parent's child
				if( pi>=0 ) {
					var parentChilds = gears[pi].childIDs;
					parentChilds.splice( parentChilds.lastIndexOf( ID ), 1);
				}
				// delete gear
				if( ID>0 ) {
					gears[ID] = null;	//.splice( ID, 1 );
					$("#gearlistitem"+ID).remove();
					$("#gearcontainer"+ID).remove();
				}
				return pi;
			}
				function getTotalChildNumber( ID ) {
					var childs = 0,
						gear = gears[ID];

					for( var i=0; i<gear.childIDs.length; i++ ) {
						childs += 1+getTotalChildNumber( gear.childIDs[i] );
					}
					return childs;
				}
				function isChildOf( chID, ID ) {
					var isChild = false,
						checkChilds = function( ID ) {
							var gear = gears[ID];
							if( gear.ID==chID ) isChild=true;
							for( var i=0; i<gear.childIDs.length; i++ ) {
								//if( gear.childIDs[i]==chID ) isChild=true;
								checkChilds( gear.childIDs[i] );
							}

						};
					checkChilds( ID );
					return isChild;
				}
				function changeID( oldID, newID ) {

					for( var i=0; i<gears.length; i++ ) {
						if( gears[i].parentID==oldID ) gears[i].parentID = newID;
						if( gears[i].ID==oldID ) gears[i].ID = newID;
						for( var c=0; c<gears[i].childIDs.length; c++ ) {
							if( gears[i].childIDs[c]==oldID ) {
								gears[i].childIDs[c] = newID;
							}
						}
					}

				}

			function rotateGears( ID ) {
				//console.log("rotate gears "+ID);
				// rotate childs (recursive)
				ID = ID || 0;
				var gear = gears[ID];
				if( ID == 0 ) { gears[ID].rot = rot-gears[ID].jointangle; }
				else {
					var parentgear = gears[ gear.parentID ],
						newrot;

					if( gear.axlejoint ) {
						gears[ID].rot = parentgear.rot-gears[ID].jointangle;	// + gear.jointangle

					} else {
						gears[ID].rot= 180-((parentgear.rot+gear.jointangle)*gear.ratio)-gear.jointangle;//-((gear.jointangle*2)*gear.ratio);

					}
					//console.log("rotation "+gears[ID].rot);
				}
				setGearDOMRotation( ID );

				for( var i=0; i<gear.childIDs.length; i++ ) {
					rotateGears( gear.childIDs[i] );
				}

			}
			function selectParent() {
				var ID = gears[selectedgear].parentID;
				if( ID>=0 ) selectGear( ID );
			}
			function selectGear( ID ) {
				selectedgear = ID;	// select this geat + set Selection!!!
				selectListItem( ID );
				setEditorValues( ID );
				setDownloadData( ID );
				$(".svg").removeClass("selected");
				$("#gearcontainer"+ID).addClass("selected");

			}
			function setDownloadData( ID ) {
				var gear = gears[ID],
					filename = "gg_gear N"+gear.N+" D"+fix2(gear.D)+" P"+fix2(gear.P)+" PA"+fix2(gear.PA)+" @"+fix2(getscale())+".svg";
				$("#svgdata").val( gear.svg );
				$("#svgfilename").val( filename );
			}
			function setEditorValues( ID ) {
				var data = gears[ID];

				setN( data.N );
				setD( data.D );
				setP( data.P );
				setPA( data.PA );
				setPG( data.parentID );
				setCA( data.jointangle );
				setCAXLE( data.axlejoint );

				//$("#out").html( '<?xml version="1.0" encoding="utf-8"?><!-- Generator: Iparigrafika SpurGearAnalyzator v2 by Abel Vincze http://iparigrafika.hu/gear -->'+data.svg );
			}
			function positionGears( ID ) {
				//console.log("rotate gears");
				// rotate childs (recursive)
				ID = ID || 0;
				var gear = gears[ID],
					parentID = gear.parentID,
					parentgear;

				//console.log( parentID );

				if( parentID>=0 ) {
					parentgear = gears[ parentID ];

					gear.ratio = parentgear.N/gears[ID].N;

					// pozicio megadasa a parent alapjan
					if( gear.axlejoint ) {
						gear.offsetx = 0;
						gear.offsety = 0;

						gear.totalratio = parentgear.totalratio;
					} else {
						var dist = parentgear.Rsc+gear.Rsc;

						gear.offsetx = Math.cos( gear.jointangle/AM )*dist;
						gear.offsety = -Math.sin( gear.jointangle/AM )*dist;

						gear.totalratio = parentgear.totalratio*gear.ratio;
					}
					gear.x = parentgear.x + gear.offsetx;
					gear.y = parentgear.y + gear.offsety;

					//console.log( gears[ID].x );

				} else {
					var temp = gear.svgwidth/2,
						sc = getscale(),
						m = Math.ceil( (temp+(sc/5))/sc );
					//gear.x = m*sc;
					  //gear.y = m*sc;
            gear.x = 833;
            gear.y = 72;

				}
				//setListItemText( ID );
				updateGearDOM( ID );

				for( var i=0; i<gear.childIDs.length; i++ ) {
					positionGears( gear.childIDs[i] );
				}

			}
			function renderAllGears() {
				renderGear(0);
				positionGears(0);
				rotateGears(0);
				makeGrid();
				maxSize();
			}
			function renderGear( ID ) {
				var gear = gears[ID];
				//console.log( "gear"+ID+" CA: "+gear.jointangle );
				updateGear( ID, gear.N, gear.D, gear.P, gear.PA, gear.jointangle );

				for( var i=0; i<gear.childIDs.length; i++ ) {
					renderGear( gear.childIDs[i] );
				}
			}
			function updatePitches() {
				var ID = selectedgear,
					P = getP(),
					PA = getPA(),
					N = getN();

				if( gears[ID].P != P || gears[ID].PA != PA ) {
					updatePitch( N, P, PA, ID );
					if( !gears[ID].axlejoint ) {
						updateParentPitch( P, PA, ID );
					}

					positionGears( 0 );
					rotateGears( 0 );
					updateHash();
					maxSize();
					//updateListItemText( ID );
					setDownloadData( ID );
				}
			}
			function updatePitch( N, P, PA, ID, excludedChild ) {
				excludedChild = excludedChild || -1;

				var gear = gears[ID],
					D = N/P;

				updateGear( ID, N, D, P, PA, gear.jointangle );

				for( var i=0; i<gear.childIDs.length; i++ ) {
					var chID = gear.childIDs[i];
					if( chID != excludedChild && !gears[chID].axlejoint ) {
						updatePitch( gears[chID].N, P, PA, chID );
					}
				}

			}
			function updateParentPitch( P, PA, ID ) {
				if( gears[ID].axlejoint ) return;
				var parentID = gears[ID].parentID;
				if( parentID>=0 ) {
					updatePitch( gears[parentID].N, P, PA, parentID, ID );
					updateParentPitch( P, PA, parentID );
				}

			}
			function updateGears() {
				var ID = selectedgear;
				updateGear( ID );
				positionGears( ID );
				rotateGears( ID );
				updateListItemText( ID );
				updateHash();
				maxSize();
				setDownloadData( ID );
			}
			function updateGear( ID, N, D, P, PA, CA ) {
				N = N || getN();
				D = D || getD();
				P = P || getP();
				PA = PA || getPA();
				CA = CA==undefined? getCA(): CA;
				var thegear = createGear( N, D, P, PA, ID );

				gears[ID].N = N;
				gears[ID].D = D;
				gears[ID].P = P;
				gears[ID].PA = PA;
				gears[ID].jointangle = CA;
				gears[ID].gearangle = thegear.gearangle;
				gears[ID].baseangle = thegear.baseangle;

				gears[ID].svg = thegear.svg;
				gears[ID].svgwidth = thegear.w;		// fogaskerek svg merete.
				gears[ID].svgheight = thegear.h;
				gears[ID].svgoffsetx = -thegear.w/2;		// svg offset a kozeppont pozicionalasahoz
				gears[ID].svgoffsety = -thegear.h/2;
				gears[ID].Rsc = thegear.Rsc;

				$("#gearcontainer"+ID).html( thegear.svg );
				setGearEvents( ID );
			}
			function setGearEvents( ID ) {
				$("#gearpoly"+ID).bind( "click", selectionClick );
			}
			function updateGearDOM( ID ) {
				var gearc = $("#gearcontainer"+ID),
					data = gears[ ID ];

				gearc.css( { width:			data.svgwidth,
							height:			data.svgheight } );
				setGearDOMRotation( ID );
			}
			function setGearDOMRotation( ID ) {
				var	gear = $("#gearcontainer"+ID),
					data = gears[ ID ];
				gear.css( { "transform": 	"translate3d("+fix2(data.x+data.svgoffsetx)+"px,"+fix2(data.y+data.svgoffsety)+"px,0) rotate("+fix6(data.rot+data.baseangle)+"deg)"  } );
				//console.log( (data.x+data.svgoffsetx)+"+"+(data.y+data.svgoffsety) )
			}
			function selectListItem( ID ) {
				$(".listitem").removeClass("selected");
				$("#gearlistitem"+ID).addClass("selected");
			}
			function setListItemText( ID ) {
				$("#gearlistitem"+ID).html( '#'+(ID)+' - ratio: '+getRatio( 1/gears[ID].totalratio )+' - RPM: '+fix2(gears[ID].totalratio*RPM) );

			}
			function updateListItemText( ID ) {
				var gear = gears[ID];

				setListItemText( ID );
				//updateGearsDOM( ID );

				for( var i=0; i<gear.childIDs.length; i++ ) {
					updateListItemText( gear.childIDs[i] );
				}

			}
				function getRatio( r ) {
					var out;
					r = Number(r);
					if( r<1 ) {
						out = "1:"+fix2(1/r);
					} else {
						out = fix2(r)+":1";
					}
					return out;
				}

			//var maxw = 0, maxh = 0;
			function maxSize() {
				var mx = 0, my = 0;

				for( var i=0, gear, gmx, gmy, add; i<gears.length; i++ ) {
					gear = gears[i];
					add = (gear.svgwidth/2)*1.5;
					gmx = gear.x+add;
					gmy = gear.y+add;
					if( gmx>mx ) mx = gmx;
					if( gmy>my ) my = gmy;
				}

				$("#cover-gears").css( { width: mx, height: my } );

			}

			// --------------------------------------------------------------------------------------------------

			function initGears() {
				$("#N").bind("enterKey",Nchange);
				$("#D").bind("enterKey",Dchange);
				$("#P").bind("enterKey",Pchange);
				$("#PA").bind("enterKey",PAchange);
				$("#scale").bind("enterKey",scaleChange);
				$("#RPM").bind("enterKey",RPMchange);
				$("#CA").bind("enterKey",CAchange);
				$("#PG").bind("enterKey",PGchange);
				$("#CAXLE").bind("change",CAXLEchange);
				$(".display").bind("change",displaychange);

				$("input").keyup(onKeyup).blur(onBlur);
				has3d = "WebKitCSSMatrix" in window || "MozPerspective" in document.body.style;
				/*@cc_on if (/^10/.test(@_jscript_version)) has3d = TRUE; @*/	//IE10 have 3d support

				resetOEF();

//        if( !parseHash() ) addGear( undefined, true, 18, 3, 6, 20 );	// default gear;
				//updateHash();
				//readCookies();
          addGearData(-1, true, 10, 0.6, 15, 20, -105);
          addGearData(0, false, 18, 1.2, 15, 20, -70, "Gamification");
          addGearData(1, false, 30, 2, 15, 20, -120, "Lean Startup");
          addGearData(2, true, 12, 0.8, 15, 20, -120, "Simple Design");
          addGearData(3, false, 30, 2, 15, 20, -50, "Test-Driven Development");
          addGearData(4, false, 14, 0.9, 15, 20, -150, "Agile");
          addGearData(5, false, 51, 3.4, 15, 20, -180, "Domain-Driven Design");
          for (var i = 0; i < 7; i++) {addGearDataProcess(i);}
					positionGears( 0 );

					rotateGears( 0 );
//					selectGear( sg );
					if( animation ) OEF();

				RPMchange();	// get initial value from input box
				maxSize();
			}
			function parseHash() {
//				  var h="#200,200,100,6,1,0,0,4,1,8,2,4,27,-90,0,0,16,4,4,27,-60,1,1,12,1,12,20,-60,2,0,60,5,12,20,0,0,0,2,-563";
					var h="#200,200,100,4,1,5,672.2000000000567,7,1,9,1.5,6,20,-105,0,0,8,1.3333333333333333,6,20,-70,1,0,16,2.6666666666666665,6,20,-35,2,1,12,0.8,15,21,-55,3,0,53,3.533333333333333,15,21,0,2,0,12,2,6,20,-155,4,0,18,1.2,15,21,-30,0,0,2,758";
				if( h ) {
					var t = h.substr( 1 ),
						CRC=0,
						CRC2=0;

					if( t=="clear" ) return false;

					t = t.split(",");

					for( var i=0; i<t.length-1; i++ ) {
						CRC += Number(t[i]);
						CRC2 = Math.sin( Number(t[i]) )*100-CRC2;
					}
					if( t[i]!=Math.ceil(CRC%800+CRC2*2) ) return false;	// Wrong CRC

					var i=0,
						gs,
						g = function() {
							return Number(t[i++]);
						},
						basex = g(),
						basey = g();

					setscale( g() );
					setRPM( g() );
					loop = animation = g()==1;
					var sg = g();
					rot = g();
					gs = g();

          for( var j=0; j<gs; j++ ) { addGearData( j==0?-1:g(), g()==1, g(), g(), g(), g(), g()); }
					for( var j=0; j<gs; j++ ) { addGearDataProcess( j ) };
					//for( var j=0; j<gs; j++ ) { updateGearDOM( j ) };
					positionGears( 0 );
					rotateGears( 0 );
					selectGear( sg );
					if( animation ) OEF();
					return true;
				}
				return false;
			}
			function updateHash() {
/*				var h  = "",
					S=",",
					CRC=0,
					CRC2=0,
					a=animation?1:0,
					g = function( n ) {
						h += n+S;
						CRC += Number(n);
						CRC2 = Math.sin( Number(n) )*100-CRC2;
					};
				g(gears[0].x);
				g(gears[0].x);
				g(getscale());
				g(getRPM());
				g(a);
				g(selectedgear);
				g(rot);
				g(gears.length);

				for( var i=0, gear; i<gears.length; i++ ) {
					gear = gears[i];
					if( i>0 ) { g(gear.parentID); }
					g(gear.axlejoint?1:0);
					g(gear.N);
					g(gear.D);
					g(gear.P);
					g(gear.PA);
					g(gear.jointangle);
				}
				g(0);	// for future use
				g(0);
				g(2);	// version
				h+=Math.ceil(CRC%800+CRC2*2);
				location.hash = "#"+h;
 */
			}
			function onKeyup( e ) {
					//console.log("key: "+e.keyCode+" shift: "+e.shiftKey );
					shift = e.shiftKey;
					if(e.keyCode == 13) {
						$(this).trigger("enterKey");
					}

			}
			function onBlur( e ) {
				$(this).trigger("enterKey");
			}
			function resetOEF() {
				window.raf = (function(){
					return 	window.requestAnimationFrame       ||
							window.webkitRequestAnimationFrame ||
							window.mozRequestAnimationFrame    ||
							function( callback ) {
								window.setTimeout( callback, 100/6 );
							};
				})();
			}
			function OEF() {
				if( animation ) {
					if( realRPM<RPM ) { realRPM += 1 }
					else if( realRPM>RPM ) { realRPM -= 1 };
					if( Math.abs(realRPM-RPM)<1 ) realRPM=RPM;
				} else {
					realRPM -= 1;
					if( realRPM<0 ) {
						realRPM=0;
						loop = false;
					}
				}
				if( loop ) raf( OEF );

				//console.log( RPM );

				rota = (realRPM/3600)*360;
				rot += rota;

 				rotateGears();
				if( loop==false ) { updateHash(); }
			}
			function anim( mode ) {
				switch( mode ) {

					case 0:
						animation = !animation
						if( animation ) {
							updateHash();
							if( !loop ) {
								loop = true;
								OEF();
							}
						}
						break;
					case 1:
						loop = false;
						animation = false;
						updateHash();
						break;
					case 2:
						loop = false;
						animation = false,
						realRPM = 0;
						rot = baserot;
						rotateGears();
						//OEF();
						updateHash();
						break;

				}

			}
			function setTheme( th ) {
				theme = th;
				$("body").attr("class", "col"+th );
				makeGrid();
				writeCookies();
			}
			function writeCookies() {
				$.cookie("theme", theme );
				$.cookie("guides", guides );
				$.cookie("geartext", geartext );
				$.cookie("grid", grid );
			}
			function readCookies() {
				var ctheme = $.cookie("theme"),
					cguides = $.cookie("guides"),
					cgeartext = $.cookie("geartext"),
					cgrid = $.cookie("grid");
				if( ctheme != undefined ) theme = ctheme;
				if( cguides != undefined ) guides = cguides=="true";
				if( cgeartext != undefined ) geartext = cgeartext=="true";
				if( cgrid != undefined ) grid = cgrid=="true";
				setguides( guides );
				setlabels( geartext );
				setgrid( grid );
				setGuidesClass();
				setLabelsClass();
				setTheme( theme );
			}
			function clearAll() {
				window.location = "http://geargenerator.com/#clear";
				window.location.reload();
			}
