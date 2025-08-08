Ce document explique ce que les scripts que j'ai faits font et les paramètres qui sont à changer.

J'ai modifié plusieurs scripts dans mon repo de lerobot, mais la plupart j'ai modifié seulement une fonction ou quelques lignes de code dans le script. Le code a été créé en se basant sur le fichier record.py

Les scripts que j'ai créés sont les suivants.

## motsaimultiple_policy.py

En théorie ce script change de policy une fois que le micro entend le mot script. Il n'a jamais été testé, donc je ne suis pas certain qu'il est fonctionnel.
Pour l'utiliser vous devez aller modifier les paramètres des robots et des policies dans le code.

1. **multiple policy**
   ```bash
   python -m lerobot.motsaimultiple_policy --robot1.type=lekiwi --robot1.id=motsaifollower --teleop1.type=so100_leader --teleop1.port=COM4 --teleop1.id=motsaileader --dataset.repo_id=Baptiste-le-Beaudry/lekiwi_mutliplepolicytest4 --dataset.single_task="lekiwi_go_to_blue_lego_and_grab" --dataset.num_episodes=1 --policy1.repo_id=Baptiste-le-Beaudry/act_lekiwi_go_to_lego --policy1.type=act --display_data=false
   ```

## motsairecord_data.py
Ce script sert à enregistrer des épisodes avec lekiwi. Vous devez modifier les paramètres de votre robot dans le code. Le code a été créé en se basant sur le fichier record.py

## motsairecord_policy.py
Ce script sert à enregistrer des épisodes avec un modèle entraîné avec lekiwi. Vous devez modifier les paramètres de votre robot dans le code. Le code a été créé en se basant sur le fichier record.py

## mergedataset.py
J'ai fait ce fichier avec chatgpt et il sert à merger deux datasets ensemble pour éventuellement faire un training sur ce gros dataset. Le seul problème est qu'il est compatible avec la version v1.6 et que maintenant nous sommes sur la v2.0, donc il n'est plus fonctionnel. Ce fichier a été fait avec l'aide de chatgpt.

## dataset/v2/run_convert.py
Ce fichier sert à exécuter le fichier convert_dataset_v1_to_v2.py. Ce fichier a été fait avec l'aide de chatgpt.

## listen.py
Ce fichier est un fichier servant à utiliser les micros sur les caméras comme outils de reconnaissance vocale. Ce fichier a été fait avec l'aide de chatgpt.

## cameras/opencv/test_cam.py
Ce fichier sert à tester les caméras. Remplacer les indices par les indices de vos caméras.

## cmd
fichier avec des commandes utiles