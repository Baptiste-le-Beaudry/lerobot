# Guide de dépannage LeRobot

Ce fichier sert à aider les utilisateurs de LeRobot quand ils sont bloqués.

## FileExistsError: [Errno 17] File exists

```
FileExistsError: [Errno 17] File exists: '/home/motsai/.cache/huggingface/lerobot/Baptiste-le-Beaudry/eval_lekiwi_go_to_lego'
```

**Solution :** Le fichier existe, supprimez le dossier ou mettez l'argument `--resume=true` en ligne de commande.

## Missing motor IDs

```
Missing motor IDs:
  - 1 (expected model: 777)
  - 2 (expected model: 777)
  - 3 (expected model: 777)
  - 4 (expected model: 777)
  - 5 (expected model: 777)
  - 6 (expected model: 777)
  - 7 (expected model: 777)
  - 8 (expected model: 777)
  - 9 (expected model: 777)

Full expected motor list (id: model_number): {1: 777, 2: 777, 3: 777, 4: 777, 5: 777, 6: 777, 7: 777, 8: 777, 9: 777}
Full found motor list (id: model_number): {}
(lerobot) motsai@robot:~/lerobot $
```

**Solution :** Cette erreur indique que vos moteurs ne sont pas alimentés, vérifiez l'alimentation ou le PCB pour les servomoteurs.

## ConnectionError: Could not connect on port

```
ConnectionError: Could not connect on port '/dev/ttyACM0'. Make sure you are using the correct port. Try running `python -m lerobot.find_port`
```

**Solution :** Ne détecte pas le port. Vous n'avez peut-être pas mis le bon nom pour le port en ligne de commande ou vérifiez s'il ne faut pas changer le nom du port directement dans le code. Peut-être que votre board est grillé, regardez la consommation du board ou le courant qui y passe et si il est chaud.

## DeviceNotConnectedError: Timeout waiting for LeKiwi Host

```
lerobot.errors.DeviceNotConnectedError: Timeout waiting for LeKiwi Host to connect expired.
```

**Solution :** Assurez-vous d'avoir démarré lekiwi_host dans le SSH. Il se peut aussi que vous n'ayez pas configuré dans le code `example/lekiwi/record` ou `robot/lekiwi/lekiwi_host` la bonne adresse IP du Raspberry Pi.

## ConnectionError: Failed to write 'Torque_Enable'

```
ConnectionError: Failed to write 'Torque_Enable' on id_=3 with '0' after 6 tries. [TxRxResult] There is no status packet! FATAL: exception not rethrown Aborted
```

**Solution :** Cette erreur survient quand un moteur est bloqué. Éteignez puis rallumez la source et bougez les moteurs pour changer leur position. Si cela arrive souvent lors d'une téléopération/record, il se peut que votre calibration ne soit pas adéquate.

## Press c to rerun the calibration

Si vous calibrez votre LeKiwi, puis démarrez un record ou autre, il vous demandera si vous voulez le recalibrer. Je vous conseille de faire "c" et enter pour refaire la calibration, car j'ai l'impression que si non il prendra l'ancien fichier de calibration.

## Problème de sortie lors de l'enregistrement d'épisodes

Si vous étiez en train d'enregistrer des épisodes puis vous ne pouvez plus sortir de la commande :

```
Left arrow key pressed. Exiting loop and rerecord the last episode...
Right arrow key pressed. Exiting loop...
Escape key pressed. Stopping data recording...
INFO 2025-08-08 14:50:29 keyboard.py:112 ESC pressed, disconnecting.
```

**Solution :** Je n'ai pas trouvé d'autre moyen que de fermer le terminal et cela se produit à cause que vous avez perdu la connexion SSH. Il doit y avoir moyen de mettre un KeyboardInterrupt à quelque part dans le code pour que ça quitte la boucle.

## TimeoutError: Timed out waiting for frame from camera

```
TimeoutError: Timed out waiting for frame from camera OpenCVCamera(/dev/video0) after 200 ms. Read thread alive: True.
```

**Solution :** Regardez si les caméras sont branchées. Exécutez le fichier `cameras/opencv/test_cam.py`, faites la même chose avec ce code.

## FileNotFoundError: config.json not found on the HuggingFace Hub in Baptiste-le-Beaudry/act2_lekiwi_go_to_lego

Les repository de lerobot ont une structure qui doit être respecté. Il est possible que votre model ne soit pas bien structuré ou que vous n'avez pas écris le bon nom de model. Noubliez pas de vous connecter à votre compte hugging face avec votre token avant.


# Si vous avez d'autre questions mon courriel est beab8213@usherbrooke.ca