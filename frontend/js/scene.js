// Three.js Scene Manager for HDT 3D Visualization - FIXED VERSION
class SceneManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.models = {};
        this.mixer = null;
        this.clock = new THREE.Clock();
        this.currentRole = null;
        
        this.init();
    }

    init() {
        console.log('🎬 Initializing 3D Scene...');
        
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);
        this.scene.fog = new THREE.Fog(0x1a1a2e, 10, 50);

        // Create camera
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
        this.camera.position.set(0, 1.6, 4);
        this.camera.lookAt(0, 1, 0);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: false
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);

        // Setup lighting
        this.setupLighting();

        // Setup controls
        this.setupControls();

        // Add ground plane
        this.addGround();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Start animation loop
        this.animate();

        console.log('✅ Three.js scene initialized');
    }

    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        // Main directional light
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        dirLight.shadow.camera.near = 0.1;
        dirLight.shadow.camera.far = 50;
        dirLight.shadow.camera.left = -10;
        dirLight.shadow.camera.right = 10;
        dirLight.shadow.camera.top = 10;
        dirLight.shadow.camera.bottom = -10;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        this.scene.add(dirLight);

        // Accent lights
        const pointLight1 = new THREE.PointLight(0x4a90e2, 0.5, 15);
        pointLight1.position.set(-4, 3, 2);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x50c878, 0.3, 15);
        pointLight2.position.set(4, 3, -2);
        this.scene.add(pointLight2);

        // Hemisphere light
        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.4);
        hemiLight.position.set(0, 20, 0);
        this.scene.add(hemiLight);
    }

    setupControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 2;
        this.controls.maxDistance = 10;
        this.controls.maxPolarAngle = Math.PI / 2 - 0.1;
        this.controls.target.set(0, 1, 0);
    }

    addGround() {
        const groundGeometry = new THREE.PlaneGeometry(20, 20);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x16213e,
            roughness: 0.8,
            metalness: 0.2
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Add grid
        const gridHelper = new THREE.GridHelper(20, 20, 0x2d3748, 0x2d3748);
        this.scene.add(gridHelper);
    }

    async loadRole(roleType) {
        console.log(`🎭 Loading role: ${roleType}`);
        this.currentRole = roleType;

        // Clear existing models
        this.clearModels();

        // Try to load the avatar
        const avatarLoaded = await this.loadAvatar(roleType);
        
        if (!avatarLoaded) {
            console.warn('⚠️ Avatar model not found, showing stylized fallback');
            this.showStylizedAvatar(roleType);
        }

        // Load environment for all roles
        await this.loadEnvironment();

        console.log('✅ Role loaded successfully');
    }

    async loadAvatar(roleType) {
        const avatarPath = `/models/avatars/${roleType}.fbx`;
        
        console.log(`📦 Attempting to load avatar from: ${avatarPath}`);
        
        // Check if FBXLoader is available
        if (typeof THREE.FBXLoader === 'undefined') {
            console.error('❌ FBXLoader not available! Check if the library is loaded.');
            return false;
        }

        try {
            const loader = new THREE.FBXLoader();
            
            const model = await new Promise((resolve, reject) => {
                loader.load(
                    avatarPath,
                    (object) => {
                        console.log('✅ FBX model loaded successfully');
                        resolve(object);
                    },
                    (xhr) => {
                        const percent = (xhr.loaded / xhr.total * 100).toFixed(1);
                        console.log(`📊 Loading avatar: ${percent}%`);
                    },
                    (error) => {
                        console.error('❌ FBX loading error:', error);
                        reject(error);
                    }
                );
            });

            // Scale and position avatar
            model.scale.set(0.01, 0.01, 0.01);
            model.position.set(0, 0, 0);

            // Enable shadows
            model.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                    
                    // Enhance materials
                    if (child.material) {
                        child.material.roughness = 0.7;
                        child.material.metalness = 0.2;
                    }
                }
            });

            this.models.avatar = model;
            this.scene.add(model);

            // Setup animations if available
            if (model.animations && model.animations.length > 0) {
                this.mixer = new THREE.AnimationMixer(model);
                const action = this.mixer.clipAction(model.animations[0]);
                action.play();
                console.log('🎬 Animation started');
            }

            return true;

        } catch (error) {
            console.warn(`⚠️ Could not load FBX avatar: ${error.message}`);
            return false;
        }
    }

    async loadEnvironment() {
        console.log('🏗️ Loading environment...');
        
        // Check if GLTFLoader is available
        if (typeof THREE.GLTFLoader === 'undefined') {
            console.error('❌ GLTFLoader not available!');
            this.createSimpleEnvironment();
            return;
        }

        try {
            // Try to load GLB models
            await this.loadGLTF('/models/environment/chair.glb', 'chair', {
                position: { x: 0, y: 0, z: 0.5 },
                scale: { x: 1, y: 1, z: 1 }
            });

            await this.loadGLTF('/models/environment/table.glb', 'table', {
                position: { x: 0, y: 0.75, z: -0.5 },
                scale: { x: 1, y: 1, z: 1 }
            });

            await this.loadGLTF('/models/environment/laptop.glb', 'laptop', {
                position: { x: 0, y: 0.85, z: -0.5 },
                scale: { x: 0.3, y: 0.3, z: 0.3 },
                rotation: { y: Math.PI }
            });

            console.log('✅ Environment models loaded');
        } catch (error) {
            console.warn('⚠️ Could not load some environment models, using simple objects');
            this.createSimpleEnvironment();
        }
    }

    async loadGLTF(path, name, transform = {}) {
        const loader = new THREE.GLTFLoader();
        
        try {
            console.log(`📦 Loading ${name} from: ${path}`);
            
            const gltf = await new Promise((resolve, reject) => {
                loader.load(
                    path,
                    resolve,
                    (xhr) => {
                        const percent = (xhr.loaded / xhr.total * 100).toFixed(1);
                        console.log(`📊 Loading ${name}: ${percent}%`);
                    },
                    reject
                );
            });

            const model = gltf.scene;

            // Apply transformations
            if (transform.position) {
                model.position.set(
                    transform.position.x || 0,
                    transform.position.y || 0,
                    transform.position.z || 0
                );
            }

            if (transform.scale) {
                model.scale.set(
                    transform.scale.x || 1,
                    transform.scale.y || 1,
                    transform.scale.z || 1
                );
            }

            if (transform.rotation && transform.rotation.y !== undefined) {
                model.rotation.y = transform.rotation.y;
            }

            // Enable shadows
            model.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            this.models[name] = model;
            this.scene.add(model);
            
            console.log(`✅ ${name} loaded successfully`);

        } catch (error) {
            console.warn(`⚠️ Could not load ${name}:`, error.message);
        }
    }

    createSimpleEnvironment() {
        console.log('🔨 Creating simple environment objects...');
        
        // Simple desk
        const deskGeometry = new THREE.BoxGeometry(2, 0.1, 1);
        const deskMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x8B4513,
            roughness: 0.8
        });
        const desk = new THREE.Mesh(deskGeometry, deskMaterial);
        desk.position.set(0, 0.75, -0.5);
        desk.castShadow = true;
        desk.receiveShadow = true;
        this.scene.add(desk);
        this.models.desk = desk;

        // Simple laptop
        const laptopGeometry = new THREE.BoxGeometry(0.4, 0.02, 0.3);
        const laptopMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x333333,
            metalness: 0.5
        });
        const laptop = new THREE.Mesh(laptopGeometry, laptopMaterial);
        laptop.position.set(0, 0.81, -0.5);
        laptop.castShadow = true;
        this.scene.add(laptop);
        this.models.laptop = laptop;
    }

    showStylizedAvatar(roleType) {
        console.log('🎨 Creating stylized avatar...');
        
        // Create avatar group
        const avatar = new THREE.Group();

        // Choose color based on role
        let color;
        switch(roleType) {
            case 'software_engineer':
                color = 0x4a90e2; // Blue
                break;
            case 'office_worker':
                color = 0x50c878; // Green
                break;
            case 'factory_worker':
                color = 0xffa500; // Orange
                break;
            default:
                color = 0x4a90e2;
        }

        const material = new THREE.MeshStandardMaterial({
            color: color,
            roughness: 0.6,
            metalness: 0.3,
            emissive: color,
            emissiveIntensity: 0.2
        });

        // Body (rounded cylinder)
        const bodyGeometry = new THREE.CylinderGeometry(0.35, 0.3, 1.4, 32);
        const body = new THREE.Mesh(bodyGeometry, material);
        body.position.y = 1;
        body.castShadow = true;
        avatar.add(body);

        // Head (sphere)
        const headGeometry = new THREE.SphereGeometry(0.25, 32, 32);
        const head = new THREE.Mesh(headGeometry, material.clone());
        head.position.y = 1.9;
        head.castShadow = true;
        avatar.add(head);

        // Arms
        const armGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.8, 16);
        
        const leftArm = new THREE.Mesh(armGeometry, material.clone());
        leftArm.position.set(-0.45, 0.9, 0);
        leftArm.rotation.z = 0.3;
        leftArm.castShadow = true;
        avatar.add(leftArm);

        const rightArm = new THREE.Mesh(armGeometry, material.clone());
        rightArm.position.set(0.45, 0.9, 0);
        rightArm.rotation.z = -0.3;
        rightArm.castShadow = true;
        avatar.add(rightArm);

        // Legs
        const legGeometry = new THREE.CylinderGeometry(0.1, 0.09, 0.9, 16);
        
        const leftLeg = new THREE.Mesh(legGeometry, material.clone());
        leftLeg.position.set(-0.15, 0.15, 0);
        leftLeg.castShadow = true;
        avatar.add(leftLeg);

        const rightLeg = new THREE.Mesh(legGeometry, material.clone());
        rightLeg.position.set(0.15, 0.15, 0);
        rightLeg.castShadow = true;
        avatar.add(rightLeg);

        // Add some glow effect
        const glowGeometry = new THREE.SphereGeometry(0.27, 32, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.position.y = 1.9;
        avatar.add(glow);

        this.models.avatar = avatar;
        this.scene.add(avatar);

        // Add idle animation
        this.addIdleAnimation(avatar);

        console.log('✅ Stylized avatar created');
    }

    addIdleAnimation(avatar) {
        // Simple breathing/idle animation
        let time = 0;
        const animate = () => {
            if (this.models.avatar === avatar) {
                time += 0.01;
                avatar.position.y = Math.sin(time) * 0.02;
                avatar.rotation.y = Math.sin(time * 0.5) * 0.05;
            }
        };
        
        this.idleAnimation = animate;
    }

    updateAvatarState(stateData) {
        if (!this.models.avatar) return;

        const { stress_level, cognitive_load, fatigue_score } = stateData;

        // Determine color based on stress level
        let color;
        if (stress_level < 30) {
            color = 0x50c878; // Green - Optimal
        } else if (stress_level < 60) {
            color = 0xffd700; // Yellow - Moderate
        } else {
            color = 0xff6b6b; // Red - Critical
        }

        // Apply color to avatar
        this.models.avatar.traverse((child) => {
            if (child.isMesh && child.material) {
                if (!child.material.emissive) {
                    child.material.emissive = new THREE.Color();
                }
                child.material.emissive.setHex(color);
                child.material.emissiveIntensity = 0.4 + (stress_level / 100) * 0.3;
            }
        });
    }

    clearModels() {
        Object.keys(this.models).forEach(key => {
            const model = this.models[key];
            if (model && this.scene) {
                this.scene.remove(model);
                
                // Dispose geometries and materials
                model.traverse((child) => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) {
                        if (Array.isArray(child.material)) {
                            child.material.forEach(mat => mat.dispose());
                        } else {
                            child.material.dispose();
                        }
                    }
                });
            }
        });
        this.models = {};
        if (this.mixer) {
            this.mixer = null;
        }
    }

    onWindowResize() {
        if (!this.camera || !this.renderer || !this.container) return;

        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();

        // Update controls
        if (this.controls) {
            this.controls.update();
        }

        // Update animations
        if (this.mixer) {
            this.mixer.update(delta);
        }

        // Update idle animation
        if (this.idleAnimation) {
            this.idleAnimation();
        }

        // Render scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    dispose() {
        this.clearModels();
        if (this.renderer) {
            this.renderer.dispose();
        }
        window.removeEventListener('resize', this.onWindowResize);
    }
}

console.log('✅ SceneManager class loaded');