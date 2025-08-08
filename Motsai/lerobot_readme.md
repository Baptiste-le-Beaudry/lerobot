# LeRobot - Guide d'utilisation

Ce fichier a pour utilité d'orienter les futurs utilisateurs de LeRobot de MOTSAI.

## Installation

Installer le dépôt avec Anaconda en suivant `docs/source/installation.mdx`

## Commencer avec votre robot

Si vous voulez vous familiariser avec LeRobot, suivre les étapes du README du robot que vous voulez utiliser avec ces paramètres :

`lerobot/docs/source/...`

## Enregistrer des datasets

⚠️ **Important** : À la date du 1er août 2025, LeRobot n'a pas implémenté de méthode pour enregistrer des épisodes et indiquer si l'épisode est bon ou pas avec LeKiwi.

Il n'y a pas de manière pour supprimer les mauvais épisodes. Il est possible de cloner le dataset localement, supprimer les infos de l'épisode à supprimer dans les JSONs, supprimer les .mp4 correspondant à l'épisode. Mais pour que l'épisode soit totalement effacé, vous devrez trouver comment supprimer les bonnes informations dans le `.cache` et potentiellement à d'autres endroits sur l'ordinateur, car j'ai remarqué que le dataset se recharge sur le hub quand on enregistre un autre dataset.

### Pour enregistrer des datasets avec LeKiwi sur le Raspberry Pi

1. **Ouvrir un PowerShell en mode SSH**

   Sur le WiFi MSR-V2 :
   ```bash
   ssh motsai@192.168.100.151
   ```

2. **Activer votre environnement Anaconda**
   ```bash
   conda activate lerobot
   ```

3. **Se diriger vers LeRobot**
   ```bash
   cd lerobot
   ```

4. **Dans un autre terminal Anaconda**, dirigez-vous vers LeRobot avec votre conda activé.

5. **Dans le PowerShell en SSH**, écrire cette commande (vous pouvez modifier l'ID) :
   ```bash
   python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=motsaikiwi
   ```

6. **Dans votre terminal Anaconda**, adaptez avec vos paramètres :
   ```bash
   python -m lerobot.motsairecord_data --display_data=false --dataset.repo_id=Baptiste-le-Beaudry/lekiwi_roll_to_legotest77 --dataset.single_task="lekiwi_roll_to_blue_lego" --dataset.num_episodes=1 --resume=true
   ```

### Contrôles pendant l'enregistrement

Lors de l'enregistrement, vous pouvez utiliser le bras leader et le clavier :

| Touche | Action |
|--------|---------|
| W | Avancer |
| A | Aller à gauche |
| S | Reculer |
| D | Aller à droite |
| Z | Tourner à gauche |
| X | Tourner à droite |
| R | Augmenter la vitesse |
| F | Diminuer la vitesse |
| → | Enregistrer l'épisode |
| ← | Recommencer l'action |

Lorsque vous avez complété un épisode, appuyez sur la **flèche droite** pour enregistrer l'épisode. Puis dans le SSH, faire `Ctrl+C` puis redémarrer `lekiwi_host` avec la même commande.

⚠️ **ATTENTION** : Si un épisode mauvais est uploadé sur le hub, il endommage la qualité du dataset. Pour l'instant, aucune manière de le supprimer. N'hésitez pas à utiliser la flèche gauche plusieurs fois et à faire `Ctrl+C`.

### Paramètres d'enregistrement

- Le `display_data` est désactivé car cela peut causer des lags
- Mettez une tâche descriptive et concise de l'action
- Laissez 1 épisode et après avoir enregistré le premier, changez le `resume` par `true`
- Il est seulement possible d'enregistrer un épisode à la fois avec ce mode, car la connexion se perd entre deux épisodes

Dans le code de `motsairecord_data.py`, les informations sur LeKiwi y sont codées. Vous pouvez les modifier dans `record()`.

### Commande alternative (moins recommandée)

```bash
python examples/lekiwi/record.py --resume --repo_id="Baptiste-le-Beaudry/lekiwi_roll_to_lego"
```

## Conseils pour les datasets

Pour faire un dataset de qualité selon Baptiste Beaudry :

- Suivre les conseils de Hugging Face : https://huggingface.co/blog/lerobot-datasets#what-makes-a-good-dataset
- Mieux la tâche est effectuée dans chaque épisode, meilleur sera le modèle
- Faire des exemples qui vont droit au but, certains rapides et d'autres plus lents
- Changer le décor ou l'orientation du Kiwi dans l'environnement souvent
- Avant d'enregistrer, effectuer cette commande pour voir si LeKiwi voit bien ce qu'il a à faire et enregistrer un dataset de test :
  ```bash
  python -m src.lerobot.cameras.opencv.test_cam
  ```
- Les datasets ayant environ 120 épisodes et plus sont ceux qui ont fait les meilleurs modèles

### Visualisation des datasets

Pour visualiser un dataset : https://lerobot-visualize-dataset.hf.space/

Aller sur la page de votre dataset puis copier le nom et coller sur le site.

**Exemple d'un bon dataset :**
- Dataset : `Baptiste-le-Beaudry/lekiwi_pick_place_lego`
- Modèle : `Baptiste-le-Beaudry/act_lekiwi_pick_and_place_lego`
- Résultat : `Baptiste-le-Beaudry/eval_lekiwi_pick_and_place_lego`

### Convention de nommage

- Les `eval_...` sont des évaluations de la policy entraînée (enregistrées en même temps que l'exécution de la policy)
- Les `act_...` sont les modèles/policies

Le nom du dataset est donné lorsque l'on effectue la commande : `Nom-utilisateur/Nom-donné-en-commande`

**Exemple :** `Baptiste-le-Beaudry/teleop_take_lego`

### Datasets et policies intéressants

| Dataset | Policy correspondante |
|---------|----------------------|
| `Baptiste-le-Beaudry/lekiwi_go_to_lego` | `Baptiste-le-Beaudry/act_lekiwi_go_to_lego` |
| `Baptiste-le-Beaudry/lekiwi_pick_place_lego` | `Baptiste-le-Beaudry/act_lekiwi_pick_and_place_lego` |
| `Baptiste-le-Beaudry/teleop_take_lego` | `Baptiste-le-Beaudry/act_teleop_take_lego` |
| `Baptiste-le-Beaudry/eval_lekiwi_pick_and_place_lego` | - |

## Entraîner une policy

Avant de lancer l'entraînement, assurez-vous d'avoir fait cette commande et d'être dans votre conda. Le mot de passe demandé est votre token Hugging Face :

```bash
huggingface-cli login
```

**Exemple de commande pour entraîner un modèle :**

```bash
python -m lerobot.scripts.train --dataset.repo_id=Baptiste-le-Beaudry/lekiwi_pick_place_lego --policy.type=act --output_dir=outputs/train/act_lekiwi_pick_place_lego --job_name=act_lekiwi_pick_place_lego --policy.device=cuda --wandb.enable=true --policy.repo_id=Baptiste-le-Beaudry/act_lekiwi_pick_place_lego
```

⏱️ **Temps d'entraînement :** Environ 5h sur l'ordinateur dans le bureau de JS.

## Exécuter un modèle

Pour exécuter un modèle avec le Raspberry Pi sur LeKiwi :

1. **Dans PowerShell en SSH :**
   ```bash
   python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=motsaikiwi
   ```

2. **Dans le terminal Conda :**
   ```bash
   python -m lerobot.motsairecord_policy --display_data=false --dataset.repo_id=Baptiste-le-Beaudry/eval_lekiwi_go_to_lego --dataset.single_task="lekiwi_go_to_blue_lego" --dataset.num_episodes=1 --policy.path=Baptiste-le-Beaudry/act_lekiwi_go_to_lego
   ```

Les paramètres de LeRobot sont codés dans le fichier `lerobot/motsairecord_policy.py` dans `record()`. Vous pouvez aller les changer.

Vous pouvez utiliser le système de flèches aussi pour pousser vos épisodes sur le hub avec **flèche droite** ou recommencer avec **flèche gauche**.

### Changement de policy en cours d'évaluation

J'ai fait un code pour changer de policy en pleine évaluation. Pour ce faire, allez changer les paramètres dans le code, puis lancez cette commande. Pour que le robot change de policy, vous devez dire **"switch"**.

```bash
python -m lerobot.motsaimultiple_policy --robot1.type=lekiwi --robot1.id=motsaifollower --teleop1.type=so100_leader --teleop1.port=COM4 --teleop1.id=motsaileader --dataset.repo_id=Baptiste-le-Beaudry/lekiwi_mutliplepolicytest4 --dataset.single_task="lekiwi_go_to_blue_lego_and_grab" --dataset.num_episodes=1 --policy1.repo_id=Baptiste-le-Beaudry/act_lekiwi_go_to_lego --policy1.type=act --display_data=false
```