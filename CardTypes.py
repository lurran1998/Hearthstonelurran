import copy
import numpy as np

def extractfrom(target, listObject):
	temp = None
	for i in range(len(listObject)):
		if listObject[i] == target:
			temp = listObject.pop(i)
			break
	return temp
	
def fixedList(listObject):
	return listObject[0:len(listObject)]
	
def copyListDict(obj, recipientMinion):
	if isinstance(obj, list):
		objCopy = []
		for element in obj:
			#check if they're basic types, like int, str, bool, NoneType, 
			if isinstance(element, (type(None), int, float, str, bool)):
				#Have tested that basic types can be appended and altering the original won't mess with the content in the list.
				objCopy.append(element)
			#随从的列表中不会引用游戏
			elif callable(element): #If the element is a function
				print("The element to copy is ", element)
				objCopy.append(copy.deepcopy(element))
			elif type(element) == list or type(element) == dict: #If the element is a list or dict, just recursively use this function.
				objCopy.append(copyListDict(element, recipientMinion))
			else: #If the element is a self-defined class. All of them have selfCopy methods.
				print("Copying self-defined obj", element)
				objCopy.append(element.selfCopy(recipientMinion))
	else:
		objCopy = {}
		for key, value in obj.items():
			if isinstance(value, (type(None), int, float, str, bool)):
				objCopy[key] = value
			#随从的列表中不会引用游戏
			elif callable(value):
				objCopy[key] = copy.deepcopy(element)
			elif type(value) == list or type(value) == dict:
				objCopy[key] = (copyListDict(value, recipientMinion))
			else:
				objCopy[key] = value.selfCopy(recipientMinion)
				
	return objCopy
	
	
class Card:
	#For Choose One cards.
	def returnTrue(self, choice=0):
		return True
		
	def returnFalse(self, choice=0):
		return False
		
	def selfManaChange(self):
		pass
		
	def randomorDiscover(self):
		return "No RNG"
		
	#This is for battlecries with specific target requirement.
	def effectCanTrigger(self):
		pass
		
	def checkEvanescent(self):
		self.evanescent = False
		for trigger in self.triggersonBoard + self.triggersinHand:
			if hasattr(trigger, "makesCardEvanescent"):
				self.evanescent = True
				break
				
	#处理卡牌进入/离开 手牌/牌库时的扳机和各个onBoard/inHand/inDeck标签
	def entersHand(self):
		self.onBoard, self.inHand, self.inDeck = False, True, False
		for trigger in self.triggersinHand:
			trigger.connect()
		return self
		
	def leavesHand(self, intoDeck=False):
		self.onBoard, self.inHand, self.inDeck = False, False, False
		#将注册了的场上、手牌和牌库扳机全部注销。
		for trigger in self.triggersonBoard:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersonBoard)
		for trigger in self.triggersinHand:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersinHand)
		for trigger in self.triggersinDeck:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersinDeck)
		#无论如果离开手牌，被移出还是洗回牌库，费用修改效果（如大帝-1）都会消失
		for manaMod in self.manaModifications:
			manaMod.getsRemoved()
		self.manaModifications = []
		
	def entersDeck(self):
		self.onBoard, self.inHand, self.inDeck = False, False, True
		#Hand_Deck.shuffleCardintoDeck won't track the mana change.
		self.Game.ManaHandler.calcMana_Single(self)
		for trigger in self.triggersinDeck:
			trigger.connect()
			
	def leavesDeck(self, intoHand=True):
		self.onBoard, self.inHand, self.inDeck = False, False, False
		#将注册了的场上、手牌和牌库扳机全部注销。
		for trigger in self.triggersonBoard:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersonBoard)
		for trigger in self.triggersinHand:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersinHand)
		for trigger in self.triggersinDeck:
			trigger.disconnect()
			if hasattr(trigger, "temp") and trigger.temp: #If the trigger is temporary, it will be removed once it leaves hand, whether being discarded, played or shuffled into deck
				extractfrom(trigger, self.triggersinDeck)
		if intoHand == False: #离开牌库时，只有去往手牌中时费用修改效果不会丢失。
			for manaMod in self.manaModifications:
				manaMod.getsRemoved()
			self.manaModifications = []
			
	"""Handle the target selection. All methods belong to minions. Other cardTypes will define their own methods."""
	def targetCorrect(self, target, choice=0):
		if target.cardType != "Minion" and target.cardType != "Hero":
			print("The target is not minion or hero.")
			return False
		if target.onBoard == False:
			print("The target is not onBoard")
			return False
		return True
		
	def selectablebySpellandHeroPower(self, subject):
		return False
		
	def selectablebyBattlecry(self, subject):
		return False
		
	def selectablebyBattle(self, subject):
		return False
		
	def targetSelectable(self, target):
		if self.cardType == "Hero Power" or self.cardType == "Spell":
			return target.selectablebySpellandHeroPower(self)
		elif self.cardType == "Minion" or self.cardType == "Weapon":
			return target.selectablebyBattlecry(self)
		return False
		
	def selectableEnemyMinionExists(self, choice=0):
		for minion in self.Game.minionsonBoard(3-self.ID):
			if self.targetSelectable(minion) and self.targetCorrect(minion, choice):
				return True
		return False
		
	def selectableFriendlyMinionExists(self, choice=0):
		for minion in self.Game.minionsonBoard(self.ID):
			if self.targetSelectable(minion) and self.targetCorrect(minion, choice):
				return True
		return False
		
	def selectableMinionExists(self, choice=0):
		return self.selectableFriendlyMinionExists(choice) or self.selectableEnemyMinionExists(choice)
		
	def selectableEnemyExists(self, choice=0):
		if self.targetCorrect(self.Game.heroes[3-self.ID]) and self.targetCorrect(self.Game.heroes[3-self.ID], choice):
			return True
		else:
			return self.selectableEnemyMinionExists()
			
	#There is always a selectable friendly character -- hero.
	def selectableFriendlyExists(self, choice=0):
		return True
		
	def selectableCharacterExists(self, choice=0):
		return self.selectableFriendlyExists(choice) or self.selectableEnemyExists(choice)
		
	#For targeting battlecries(Minions/Weapons)
	def targetExists(self, choice=0):
		return True
		
	def selectionLegit(self, target, choice=0):
		#抉择牌在有全选光环时，选项自动更正为"ChooseBoth"
		if self.chooseOne > 0:
			if self.Game.playerStatus[self.ID]["Choose Both"] > 0:
				choice = "ChooseBoth"
			elif choice < 0 or choice >= len(self.options):
				print("Choose One card given an invalid choice: ", choice)
				return False
		else:
			choice = 0
			
		print("Verifying the validity of selection. Subject %s, target"%self.name, target, " with choice ", choice)
		if target != None: #指明了目标
			#在指明目标的情况下，只有抉择牌的选项是合理的，选项需要目标，目标对于这个选项正确，且目标可选时，才能返回正确。
			if self.needTarget(choice) == False:
				print("The card doesn't need target.")
				return False
			if self.targetCorrect(target, choice) == False:
				print("The card is given a wrong target.")
				return False
			if self.targetSelectable(target) == False:
				print("The target is not selectable to the card.")
				return False
			return True
		else: #No target selected.
			#法术，武器和英雄技能如果是指向性的必须要有指定目标才可能使用。
			if self.cardType == "Spell" or self.cardType == "Weapon" or self.cardType == "Hero Power":
				if self.needTarget(choice) == False:
					return True
				else:
					print("Targeting spell/weapon/hero requires target to be played.")
			elif self.cardType == "Minion": #随从可以在战吼非指向或者没有战吼目标的情况下使用。
				if self.needTarget(choice) == False or self.targetExists(choice) == False:
					return True
				else:
					print("Minion with targeting battlecry must select a target when possible.")
			else: #英雄牌目标没有需要指定目标的，所以可以直接返回True
				return True
				
		return False
		
	def whenEffective(self, target=None, comment="", choice=0):
		return self, target
		
	"""Handle the card doing battle(Minion and Hero)"""
	#Game.battleRequest() invokes this function.
	def attacks(self, target, consumeAttackChance=True):
		print(self.name, " attacks ", target.name)
		subject_attack, target_attack = max(0, self.attack), max(0, target.attack)
		if self.cardType == "Minion":
			self.keyWords["Stealth"] = 0
		self.status["Temp Stealth"] = 0
		#Manipulate the health of the subject/target's health.
		#Only send out "MinionTakesDamage" signal at this point.
		if consumeAttackChance:
			self.attTimes += 1
			
		damageDealingList = []
		#如果攻击者是英雄且装备着当前回合打开着的武器，则将攻击的伤害来源视为那把武器。
		if self.cardType == "Hero" and self.Game.availableWeapon(self.ID) != None and self.ID == self.Game.turn:
			damageDealer_attacker = self.Game.availableWeapon(self.ID)
		else:
			damageDealer_attacker = self
		#如果被攻击者是英雄，且装备着当前回合打开着的武器，则将攻击目标造成的伤害来源视为那把武器。
		if target.cardType == "Hero" and self.Game.availableWeapon(target.ID) != None and target.ID == self.Game.turn:
			damageDealer_target = self.Game.availableWeapon(target.ID)
		else:
			damageDealer_target = target
			
		#首先结算攻击者对于攻击目标的伤害，如果攻击力小于1，则攻击目标不会被记入伤害处理列表。
		#注意这个伤害承受目标不一定是攻击目标，因为有博尔夫碎盾以及钳嘴龟持盾者的存在
		#承受伤害者的血量减少，结算剧毒，但是此时不会发出受伤信号。
		objtoTakeDamage = self.Game.DamageHandler.damageTransfer(target)
		if objtoTakeDamage.damageRequest(damageDealer_attacker, subject_attack) > 0:
			damageActual, survival = objtoTakeDamage.takesDamage(damageDealer_attacker, subject_attack, sendDamageSignal=False)
			damageDealingList.append((damageDealer_attacker, objtoTakeDamage, damageActual))
		
		#寻找受到攻击目标的伤害的角色。同理，此时受伤的角色不会发出受伤信号，这些受伤信号会在之后统一发出。
		objtoTakeDamage = self.Game.DamageHandler.damageTransfer(self)
		if objtoTakeDamage.damageRequest(damageDealer_target, target_attack) > 0:
			damageActual, survival = objtoTakeDamage.takesDamage(damageDealer_target, target_attack, sendDamageSignal=False)
			damageDealingList.append((damageDealer_target, objtoTakeDamage, damageActual))
		#如果攻击者的伤害来源（随从或者武器）有对相邻随从也造成伤害的扳机，则将相邻的随从录入处理列表。
		if damageDealer_attacker.cardType != "Hero" and damageDealer_attacker.marks["Attack Adjacent Minions"] > 0 and target.cardType == "Minion":
			adjacentMinions = self.Game.findAdjacentMinions(target)[0] #此时被攻击的随从一定是在场的，已经由Game.battleRequest保证。
			for minion in adjacentMinions:
				objtoTakeDamage = self.Game.DamageHandler.damageTransfer(minion)
				if objtoTakeDamage.damageRequest(damageDealer_attacker, subject_attack) > 0:
					damageActual, survival = objtoTakeDamage.takesDamage(damageDealer_attacker, subject_attack, sendDamageSignal=False)
					damageDealingList.append((damageDealer_attacker, objtoTakeDamage, damageActual))
					
		if damageDealer_attacker.cardType == "Weapon":
			damageDealer_attacker.loseDurability()
		for damageDealer, objtoTakeDamage, damage in damageDealingList:
			#参与战斗的各方在战斗过程中只减少血量，受伤的信号在血量和受伤名单登记完毕之后按被攻击者，攻击者，被涉及者顺序发出。
			self.Game.sendSignal(objtoTakeDamage.cardType+"TakesDamage", self.Game.turn, damageDealer, objtoTakeDamage, damage, "")
			self.Game.sendSignal(objtoTakeDamage.cardType+"TookDamage", self.Game.turn, damageDealer, objtoTakeDamage, damage, "")
			#吸血扳机始终在队列结算的末尾。
			print("Damage dealer %s attempts to Lifesteal "%damageDealer.name, damage)
			damageDealer.tryLifesteal(damage)
			
	"""Handle cards dealing targeting/AOE damage/heal to target(s)."""
	#Handle Lifesteal of a card. Currently Minion/Weapon/Spell classs have this method.
	##法术因为有因为外界因素获得吸血的能力，所以有自己的tryLifesteal方法。
	def tryLifesteal(self, damage):
		if self.keyWords["Lifesteal"] > 0 or (self.cardType == "Spell" and self.Game.playerStatus[self.ID]["Spells Have Lifesteal"] > 0):
			heal = damage * (2 ** self.countHealDouble())
			print(self.name, "deals %d damage and restores %d Health to player"%(damage, heal))
			if self.Game.playerStatus[self.ID]["Heal to Damage"] > 0:
				#If the Lifesteal heal is converted to damage, then the obj to take the final 
				#damage will not cause Lifesteal cycle.
				objtoTakeDamage_Auchenai = self.Game.DamageHandler.damageTransfer(self.Game.heroes[self.ID])
				if objtoTakeDamage_Auchenai.damageRequest(self, heal) > 0:
					objtoTakeDamage_Auchenai.takesDamage(self, heal)
			else: #Heal is heal.
				self.Game.heroes[self.ID].getsHealed(self, heal)
				
	#可以对在场上以及手牌中的随从造成伤害，同时触发应有的响应，比如暴乱狂战士和+1攻击力和死亡缠绕的抽牌。
	#牌库中的和已经死亡的随从免疫伤害，但是死亡缠绕可以触发抽牌。
	#吸血同样可以对于手牌中的随从生效并为英雄恢复生命值。如果手牌中的随从有圣盾，那个圣盾可以抵挡伤害，那个随从在打出后没有圣盾（已经消耗）。
	#没有超杀战吼，所以不必考虑triggers["DealsDamage"]。
	#暂时可以考虑不把吸血做成场上扳机，因为几乎没有战吼随从可以获得吸血，直接将吸血视为随从的dealsDamage自带属性也可以。
	def dealsDamage(self, target, damage):
		if target.onBoard or target.inHand:
			objtoTakeDamage = self.Game.DamageHandler.damageTransfer(target)
			targetSurvival = objtoTakeDamage.damageRequest(self, damage)
			if targetSurvival > 0:
				#超杀和造成伤害触发的效果为场上扳机.吸血始终会在队列的末尾结算。
				#战斗时不会调用这个函数，血量减少时也不立即发生伤害信号，但是这里是可以立即发生信号触发扳机的。
				#如果随从或者英雄处于可以修改伤害的效果之下，如命令怒吼或者复活的铠甲，伤害量会发生变化
				damageActual, survival = objtoTakeDamage.takesDamage(self, damage)
				self.tryLifesteal(damageActual)
				
			return objtoTakeDamage, targetSurvival
			
		else: #The target is neither on board or in hand. Either removed already or shuffled into deck.
			if target.dead and target.inDeck == False:
				return target, 2 #There is no battlecry that has overkill, no need to return 3.
			elif target.inDeck:
				return None, 0 #Minions in deck won't receive any damage and effect following it.
				
	#The targets can be [], [subject], [subject1, subject2, ...]		
	#For now, AOE will only affect targets that are on board. No need to check if the target is dead, in hand or in deck.
	#当场上有血量为2的奥金尼和因为欧米茄灵能者获得的法术吸血时，神圣新星杀死奥金尼仍然会保留治疗转伤害的效果。
	#有的扳机随从默认随从需要在非濒死情况下才能触发扳机，如北郡牧师。
	def dealsAOE(self, targets_Damage, damages, targets_Heal=[], heals=[]):
		#AOE也是首先计算血量变化，之后才发出治疗或者是伤害信号。
		#The heals are converted to damages.
		targets_Damage, damages = fixedList(targets_Damage), fixedList(damages)
		targets_Heal, heals = fixedList(targets_Heal), fixedList(heals)
		if self.Game.playerStatus[self.ID]["Heal to Damage"] > 0:
			targets_Damage += targets_Heal
			damages += heals
			targets_damaged, damagesConnected, targets_Healed, healsConnected = self.Game.AOE_preprocess(self, targets_Damage, damages)
			targets_damaged, damagesActual, targets_Healed, healsActual, totalDamageDone, totalHealingDone, damageSurvivals = self.Game.AOE(self, targets_damaged, damagesConnected)
		else: #The heals are heals.
			targets_damaged, damagesConnected, targets_Healed, healsConnected = self.Game.AOE_preprocess(self, targets_Damage, damages, targets_Heal, heals)
			targets_damaged, damagesActual, targets_Healed, healsActual, totalDamageDone, totalHealingDone, damageSurvivals = self.Game.AOE(self, targets_damaged, damagesConnected, targets_Healed, healsConnected)
			
		self.tryLifesteal(totalDamageDone)
		return targets_damaged, damagesActual, targets_Healed, healsActual, totalDamageDone, totalHealingDone, damageSurvivals
		
	def restoresHealth(self, target, heal):
		if self.Game.playerStatus[self.ID]["Heal to Damage"] > 0:
			objtoTakeDamage, targetSurvival = self.dealsDamage(target, heal)
			return objtoTakeDamage, targetSurvival
		else:
			targetSurvival = target.getsHealed(self, heal)
			return target, targetSurvival
			
	def destroyMinion(self, target):
		if target.onBoard:
			target.dead = True
		elif target.inHand:
			self.Game.Hand_Deck.discardCard(target.ID, target)
			
	"""Handle the battle options for minions and heroes."""
	def returnBattleTargets(self):
		targets = []
		if self.canAttack():
			if self.canAttackTarget(self.Game.heroes[3-self.ID]):
				targets.append(self.Game.heroes[3-self.ID])
			for minion in self.Game.minionsonBoard(3-self.ID):
				if self.canAttackTarget(minion):
					targets.append(minion)
					
		return targets
		
	#To be invoked by AI and Shudderwock
	def returnTargets(self, comment="", choice=0):
		targets = []
		if comment == "":
			if self.targetSelectable(self.Game.heroes[1]) and self.targetCorrect(self.Game.heroes[1], choice):
				targets.append(self.Game.heroes[1])
			if self.targetSelectable(self.Game.heroes[2]) and self.targetCorrect(self.Game.heroes[2], choice):
				targets.append(self.Game.heroes[2])
			for minion in self.Game.minionsonBoard(1) + self.Game.minionsonBoard(2):
				if self.targetSelectable(minion) and self.targetCorrect(minion, choice):
					targets.append(minion)
					
		elif comment == "IgnoreStealthandImmune":
			if self.targetCorrect(self.Game.heroes[1], choice):
				targets.append(self.Game.heroes[1])
			if self.targetCorrect(self.Game.heroes[2], choice):
				targets.append(self.Game.heroes[2])
			for minion in self.Game.minionsonBoard(1) + self.Game.minionsonBoard(2):
				if self.targetCorrect(minion, choice):
					targets.append(minion)
					
		return targets
		
	#Minion has its own selfCopy() method.
	#For now, copying non-minion cards can only create copies that don't have any enchantments on it.
	#The mana of a card can be copied, though.
	def selfCopy(self, ID):
		Copy = type(self)(self.Game, ID)
		Copy.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		#复制一张牌的费用修改情况
		for manaMod in self.manaModifications:
			mod = copy.deepcopy(manaMod)
			mod.card = Copy
			mod.applies()
		return Copy
		
		
		
class Permanent(Card):
	Class, name = "Neutral", "Vanilla"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.Class = type(self).Class
		self.name = type(self).name
		self.cardType = "Permanent"
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.dead = False
		self.sequence, self.position = -1, -2
		self.race = ""
		self.keyWords = {"Taunt": 0,
						"Divine Shield": 0,
						"Stealth": 0,
						"Lifesteal": 0,
						"Windfury": 0,
						"Mega Windfury": 0,
						"Spell Damage": 0,
						"Charge": 0,
						"Rush": 0,
						"Poisonous": 0,
						"Echo": 0
						}
		self.marks = {"Attack Adjacent Minions": 0,
						"Evasive": 0,
						"Enemy Evasive": 0,
						"Can't Attack": 0,
						"Can't Attack Hero": 0,
						"Double Heal": 0, #Crystalsmith Kangor
						"Hero Power Double Heal and Damage": 0, #Prophet Velen, Clockwork Automation
						"Spell Double Heal and Damage": 0
						}
		self.status = {"Immune": 0,
						"Frozen": 0,
						"Temp Stealth": 0,
						"Temp Controlled": 0
						}
		self.auras = {}
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		
	def appears(self):
		print("Permanent", self.name, "appears on board.")
		self.onBoard, self.inHand, self.inDeck = True, False, False
		self.dead = False
		#目前没有Permanent有光环
		for value in self.auras.values():
			print("Now starting %s's Aura", value)
			value.auraAppears()
		#随从入场时将注册其场上扳机。
		for trigger in self.triggersonBoard:
			trigger.connect() #把(obj, signal)放入Game.triggersonBoard中
			
	#Permanent本身是没有死亡扳机的，所以这个keepDeathrattlesRegistered无论真假都无影响
	def disappears(self, keepDeathrattlesRegistered=False):
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.dead = False
		#Only the auras and disappearResponse will be invoked when the minion switches side.
		for value in self.auras.values():
			value.auraDisappears()
		#随从离场时清除其携带的普通场上扳机，但是此时不考虑亡语扳机
		for trigger in self.triggersonBoard:
			trigger.disconnect()
			
	def turnStarts(self, ID):
		pass
		
	def turnEnds(self, ID):
		pass
		
	def canAttack(self):
		return False
		
	def damageRequest(self, subject, damage):
		return 0
		
		
class Minion(Card):
	Class, race, name = "Neutral", "", "Vanilla"
	mana, attack, health = 2, 2, 2
	index = "Vanilla-Neutral-2-2-2-Minion-None-Vanilla-Uncollectible"
	needTarget, keyWord, description = False, "", ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.Class, self.name = type(self).Class, type(self).name
		self.cardType, self.race = "Minion", type(self).race
		#卡牌的费用和对于费用修改的效果列表在此处定义
		self.mana, self.manaModifications = type(self).mana, []
		self.attack, self.attack_0 = type(self).attack, type(self).attack
		self.health_0, self.health, self.health_upper = type(self).health, type(self).health, type(self).health
		self.tempAttackChanges = [] #list of (tempAttChange, expiration timepoint)
		#The stat of a minion are classified as:
			#self.attack_0; self.attack_Enchant; self.attack(affected by buffAura and tempChange)
			#self.attack_0; self.health_Enchant; self.health, self.health_upper.
		self.attack_Enchant, self.health_Enchant = self.attack, self.health
		self.stat_AuraAffected = [0, 0, []] #The list contains all the Aura Objs put on this minion.
		self.keyWords_AuraAffected = {"Charge":0, "Rush":0, "Mega Windfury":0,
										"Auras":[]}
		self.description = type(self).description
		#当一个实例被创建的时候，其needTarget被强行更改为returnTrue或者是returnFalse，不论定义中如何修改needTarget(self, choice=0)这个函数，都会被绕过。需要直接对returnTrue()函数进行修改。
		self.needTarget = self.returnTrue if type(self).needTarget else self.returnFalse
		self.keyWords = {"Taunt": 0, "Divine Shield": 0, "Stealth": 0,
						"Lifesteal": 0,	"Spell Damage": 0, "Poisonous": 0,
						"Windfury": 0, "Mega Windfury": 0, "Charge": 0, "Rush": 0,
						"Echo": 0, "Reborn": 0,
						}
		if type(self).keyWord != "":
			for key in type(self).keyWord.split(","):
				self.keyWords[key] = 1
		#Some state of the minion represented by the marks
		self.marks = {"Attack Adjacent Minions": 0,
						"Evasive": 0,
						"Enemy Evasive": 0,
						"Can't Attack": 0,
						"Can't Attack Hero": 0,
						"Double Heal": 0, #Crystalsmith Kangor
						"Hero Power Double Heal and Damage": 0, #Prophet Velen, Clockwork Automation
						"Spell Double Heal and Damage": 0
						}
		#Temp effects that vanish at certain points.
		self.status = {"Immune": 0,
						"Frozen": 0,
						"Temp Stealth": 0,
						"Temp Controlled": 0
						}
						
		self.dead = False
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.auras = {}
		self.options = [] #For Choose One minions.
		self.overload, self.chooseOne, self.magnetic = 0, 0, 0
		self.effectViable, self.evanescent = False, False
		self.newonthisSide = True
		self.attTimes, self.attChances_base, self.attChances_extra = 0, 0, 0
		self.silenced = False
		self.activated = False #This mark is for minion state change, such as enrage.
		#self.sequence records the number of the minion's appearance.
		#The first minion on board has a sequence of 0
		self.sequence, self.position = -1, 2
		#Princess Talanji needs to confirm if a card started in original deck.
		#First two are for card authenticity verification. The last is to check if the minion has ever left board.
		self.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		
		self.triggers = {"Discarded":[], "StatChanges":[], "Drawn":[]}
		self.appearResponse, self.disappearResponse, self.silenceResponse = [], [], []
		self.deathrattles = [] #随从的亡语的触发方式与场上扳机一致，诸扳机之间与
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.history = {"Spells Cast on This": [],
						"Magnetic Upgrades": {"AttackGain": 0, "HealthGain": 0,
												"Keywords":{}, "Marks":{},
												"Deathrattles":[], "Triggers":[]
												}
						}
						
	"""Handle the triggersonBoard/inHand/inDeck of minions based on its move"""
	def appears(self):
		print(self.name, " appears on board.")
		self.newonthisSide = True
		self.onBoard, self.inHand, self.inDeck = True, False, False
		self.dead = False
		self.mana = type(self).mana #Restore the minion's mana to original value.
		self.decideAttChances_base() #Decide base att chances, given Windfury and Mega Windfury
		for value in self.auras.values():
			print("Now starting minion %s's Aura", value)
			value.auraAppears()
		#随从入场时将注册其场上扳机和亡语扳机
		for trigger in self.triggersonBoard + self.deathrattles:
			trigger.connect() #把(obj, signal)放入Game.triggersonBoard中
		#Mainly mana aura minions, e.g. Sorcerer's Apprentice.
		for func in self.appearResponse:
			func()
		#The buffAuras/hasAuras will react to this signal.
		self.Game.sendSignal("MinionAppears", self.ID, self, None, 0, "")
		for func in self.triggers["StatChanges"]: #For Lightspawn and Paragon of Light
			func()
			
	def disappears(self, keepDeathrattlesRegistered=True): #The minion is about to leave board.
		self.onBoard, self.inHand, self.inDeck = False, False, False
		#Only the auras and disappearResponse will be invoked when the minion switches side.
		for value in self.auras.values():
			value.auraDisappears()
		#随从离场时清除其携带的普通场上扳机，但是此时不考虑亡语扳机
		for trigger in self.triggersonBoard:
			trigger.disconnect()
		#随从因离场方式不同，对于亡语扳机的注册是否保留也有不同
			#死亡时触发的区域移动扳机导致的返回手牌或者牌库--保留其他死亡扳机的注册
			#存活状态下因为亡语触发效果而触发的区域移动扳机--保留其他死亡扳机
			#存活状态下因为闷棍等效果导致的返回手牌--注销全部死亡扳机
			#存活状态下因为控制权变更，会取消全部死亡扳机的注册，在随从移动到另一侧的时候重新注册死亡扳机
		#总之，区域移动扳机的触发不会取消其他注册了的死亡扳机,这些死亡扳机会在它们触发之后移除。
		#如果那些死亡扳机是因为其他效果而触发（非死亡），除非随从在扳机触发后已经离场（返回手牌或者牌库），否则可以保留
		if keepDeathrattlesRegistered == False:
			for trigger in self.deathrattles:
				trigger.disconnect()
		#如果随从有离场时需要触发的函数，在此处理
		for func in self.disappearResponse:
			func()
		#Let buffAura_Receivers remove themselves
		while self.stat_AuraAffected[2] != []:
			self.stat_AuraAffected[2][0].effectClear()
		#Let hasAura_Receivers remove themselves
		while self.keyWords_AuraAffected["Auras"] != []:
			self.keyWords_AuraAffected["Auras"][0].effectClear()
			
		self.Game.sendSignal("MinionDisappears", self.ID, None, self, 0, "")
		
	"""Attack chances handle"""
	#The game will directly invoke the turnStarts/turnEnds methods.
	def turnStarts(self, ID):
		if ID == self.ID:
			if self.onBoard: #Only minions onBoard will lose the temp Stealth
				self.status["Temp Stealth"] = 0
			self.newonthisSide = False
			self.attTimes, self.attChances_extra = 0, 0
			self.decideAttChances_base()
			size = len(self.tempAttackChanges) #Remove the temp attack changes.
			for i in range(size):
				if self.tempAttackChanges[size-1-i][1] == "StartofTurn 1" and self.Game.turn == 1:
					self.statChange(-self.tempAttackChanges[size-1-i][0], 0)
					self.tempAttackChanges.pop(size-1-i)
				if self.tempAttackChanges[size-1-i][1] == "StartofTurn 2" and self.Game.turn == 2:
					self.statChange(-self.tempAttackChanges[size-1-i][0], 0)
					self.tempAttackChanges.pop(size-1-i)
					
	#Violet teacher is frozen in hand. When played right after being frozen or a turn after that, it can't defrost.
	#The minion is still frozen when played. And since it's not actionable, it won't defrost at the end of turn either.
	#随从不能因为有多次攻击机会而自行解冻。只能等回合结束。
	def turnEnds(self, ID):
		if ID == self.ID:
			self.status["Immune"] = 0
			#The minion can only thaw itself at the end of its turn. Not during or outside its turn
			if self.onBoard and self.status["Frozen"] > 0: #The minion can't defrost in hand.
				if self.actionable() and self.attChances_base + self.attChances_extra  > self.attTimes:
					self.status["Frozen"] = 0
					
			self.newonthisSide = False
			self.attTimes, self.attChances_extra = 0, 0
		#直到回合结束的对攻击力改变效果不论是否是该随从的当前回合，都会消失
		size = len(self.tempAttackChanges)
		for i in range(size):
			if self.tempAttackChanges[size-1-i][1] == "EndofTurn":
				self.statChange(-self.tempAttackChanges[size-1-i][0], 0)
				self.tempAttackChanges.pop(size-1-i)
					
	def statusPrint(self):
		print("Minion: %s. Description:"%self.name, self.description)
		#print("Minion ID:", self.ID)
		#print("Minion onBoard: ", self.onBoard, " inHand: ", self.inHand, " in deck: ", self.inDeck)
		#print(self.name, "is new on this side: ", self.newonthisSide, " and is temporarily controlled ", self.status["Temp Controlled"])
		#print(self.name, "is allowed to attack: ", self.canAttack())
		print(self.name, ": Attacked times : %d.	Base attack chances left: %d.	Extra attack chances left: "%(self.attTimes, self.attChances_base), self.attChances_extra)
		keyWords = []
		for key, value in self.keyWords.items():
			if value > 0:
				keyWords.append(key)
		if keyWords != []:
			print("Minion has keyword:", keyWords)
		statusList = []
		for key, value in self.status.items():
			if value > 0:
				statusList.append(key)
		if statusList != []:
			print("Minion status:", statusList)
		if self.triggersonBoard != []:
			print("Minion's triggersonBoard")
			for trigger in self.triggersonBoard:
				print(type(trigger))
		if self.triggersinHand != []:
			print("Minion's triggersinHand")
			for trigger in self.triggersinHand:
				print(type(trigger))
		if self.triggersinDeck != []:
			print("Minion's triggersinDeck")
			for trigger in self.triggersinDeck:
				print(type(trigger))
		if self.auras != {}:
			print("Minion's aura: ")
			for key, value in self.auras.items():
				print(key, ": ", value)
		if self.stat_AuraAffected[2] != [] or self.keyWords_AuraAffected["Auras"] != []:
			print("Effects of auras on minion")
			print(self.stat_AuraAffected)
			print(self.keyWords_AuraAffected)
		if self.deathrattles != []:
			print("Minion's Deathrattles:")
			for trigger in self.deathrattles:
				print(type(trigger))
				
	#判定随从是否处于刚在我方场上登场，以及暂时控制、冲锋、突袭等。
	def actionable(self):
		#不考虑冻结、零攻和自身有不能攻击的debuff的情况。
		if self.ID == self.Game.turn:
			#如果随从是刚到我方场上，则需要分析是否是暂时控制或者是有冲锋或者突袭。
			if self.newonthisSide:
				if self.status["Temp Controlled"] > 0 or self.keyWords["Charge"] > 0 or self.keyWords["Rush"] > 0:
					return True
			else: #随从已经在我方场上存在一个回合。则肯定可以行动。
				return True
		return False
		
	def decideAttChances_base(self):
		if self.keyWords["Mega Windfury"] > 0:
			self.attChances_base = 4
		elif self.keyWords["Windfury"] > 0:
			self.attChances_base = 2
		else:
			self.attChances_base = 1
			
	def getsFrozen(self):
		self.status["Frozen"] += 1
		print(self.name, "gets Frozen.")
		self.Game.sendSignal("MinionGetsFrozen", self.Game.turn, None, self, 0, "")
		
	def getsKeyword(self, keyWord):
		if (self.onBoard or self.inHand): # and keyWord in self.keyWords.keys()
			self.keyWords[keyWord] += 1
			if self.onBoard:
				self.decideAttChances_base()
				if keyWord == "Charge":
					self.Game.sendSignal("MinionChargeKeywordChange", self.Game.turn, self, None, 0, "")
				self.statusPrint()
				
	#当随从失去关键字的时候不可能有解冻情况发生。
	def losesKeyword(self, keyWord):
		if self.onBoard or self.inHand:
			if self.keyWords[keyWord] > 0:
				self.keyWords[keyWord] -= 1
			if keyWord == "Divine Shield":
				self.keyWords["Divine Shield"] = 0
				self.Game.sendSignal("MinionLosesDivineShield", self.Game.turn, None, self, 0, "")
			if self.onBoard:
				self.decideAttChances_base()
				if keyWord == "Charge":
					self.Game.sendSignal("MinionChargeKeywordChange", self.Game.turn, self, None, 0, "")
				self.statusPrint()
				
	def afterSwitchSide(self, activity):
		self.newonthisSide = True
		self.decideAttChances_base()
		if activity == "Borrow":
			self.status["Temp Controlled"] = 1
		else: #activity == "Permanent" or "Return"
			self.status["Temp Controlled"] = 0
		self.statusPrint()
		
	#Whether the minion can select the attack target or not.
	def canAttack(self):
		if self.actionable() == False or self.attack < 1 or self.status["Frozen"] > 0:
			return False
		#THE CHARGE/RUSH MINIONS WILL GAIN ATTACKCHANCES WHEN THEY APPEAR
		if self.attChances_base + self.attChances_extra <= self.attTimes:
			return False
		if self.marks["Can't Attack"] > 0:
			return False
		return True
		
	def canAttackTarget(self, target):
		if self.canAttack() == False:
			return False
		if target.selectablebyBattle(self) == False:
			print(target.name, " is not selectable by attack.")
			return False
		#在actionable为True且目标可选的情况下只用一种情况下随从不能攻击一个角色： 突袭不能攻击英雄。
		#刚登场回合，如果不是有冲锋或者是被暂时控制，则一个随从不能攻击对方英雄。
		if self.newonthisSide and self.status["Temp Controlled"] < 1 and self.keyWords["Charge"] < 1 and target.cardType == "Hero":
			print(self.name, " has rush but the target is not minion.")
			return False
			
		if self.marks["Can't Attack Hero"] > 0 and target.cardType == "Hero":
			print("The minion is not allowed to attack hero")
			return False
			
		return True
		
	"""Healing, damage, takeDamage, AOE, lifesteal and dealing damage response"""
	#Decides if the minion will take damage or not. Divine Shield will be resolved.
	#如果该随从在手牌中且拥有圣盾，则被返回手牌后，如果被造成伤害，则在手中失去圣盾。血量不变，不会触发伤害施加者的吸血。
	def damageRequest(self, subject, damage):
		if damage <= 0:
			return 0 #Survival status
		else:
			if self.status["Immune"] > 0:
				print(self.name, " is immune and takes no damage.")
				return 0
			else:
				if self.keyWords["Divine Shield"] > 0:
					print("Divine shield prevents %s from taking damage."%self.name)
					self.losesKeyword("Divine Shield")
					return 0
				else:#如果伤害大于0，且没有免疫和圣盾可以阻止伤害的发生。
					#命令怒吼状态下，随从如果处于1点生命值或以下，防止那个伤害。
					if self.Game.playerStatus[self.ID]["Commanding Shout"] > 0:
						if self.health <= 1:
							return 0
						else:
							if subject.keyWords["Poisonous"] > 0: #Poisonous can still kill the minion
								return 2
							else: #If not poisonous, the minion won't be killed.
								return 1
					else: #非命令怒吼状态下，进行正常的结算。
						if damage > self.health:
							return 3 #Overkilled
						elif damage == self.health:
							return 2
						else:
							if subject.keyWords["Poisonous"] > 0:
								return 2
							else:
								return 1
								
	#Stealth Dreadscale actually stays in stealth.
	def takesDamage(self, subject, damage, sendDamageSignal=True):
		if self.Game.playerStatus[self.ID]["Commanding Shout"] > 0:
			if self.health > 1: #命令怒吼状态下只有生命值大于1的随从会受到真实伤害。
				damage = min(damage, self.health - 1)
			else:
				damage = 0
				
		if damage <= 0:
			survival = 0
		else:
			#经过检测，被伏击者返回手牌中的紫罗兰老师不会因为毒药贩子加精灵弓箭手而直接丢弃。会减1血，并在打出时复原。
			if subject.keyWords["Poisonous"] > 0 and self.onBoard:
				self.dead = True
			if self.health  < damage:
				survival = 3
			elif self.health == damage:
				survival = 2
			else:
				if subject.keyWords["Poisonous"] > 0:
					print(self.name, " is killed by the Poisonous from", subject.name)
					survival = 2
				else:
					survival = 1
					
			self.health -= damage
			#在同时涉及多个角色的伤害处理中，受到的伤害暂不发送信号而之后统一进行扳机触发。
			if sendDamageSignal:
				self.Game.sendSignal("MinionTakesDamage", self.Game.turn, subject, self, damage, "")
				self.Game.sendSignal("MinionTookDamage", self.Game.turn, subject, self, damage, "")
			#随从的激怒，根据血量和攻击的状态改变都在这里触发。
			for func in self.triggers["StatChanges"]:
				func()
				
		return damage, survival
		
	#Lifesteal will only calc once with Aukenai,  for a lifesteal damage spell, 
	#the damage output is first enhanced by spell damage.=, then the lifesteal is doubled by Kangor, then the doubled healing is converted by the Aukenai.
	def getsHealed(self, subject, heal, sendHealSignal=True):
		if self.inHand or self.onBoard:
			if self.health == self.health_upper:
				print("Minion %s at full health already."%self.name)
				return 0, 0
			else:
				if self.health + heal < self.health_upper:
					self.health += heal
					self.Game.CounterHandler.healthRestoredThisGame[subject.ID] += heal
					if sendHealSignal: #During AOE healing, the signals are delayed.
						self.Game.sendSignal("MinionGetsHealed", self.Game.turn, subject, self, heal, "StillDamaged")
					for func in self.triggers["StatChanges"]:
						func()
					return heal, -1
				else:
					healDone = self.health_upper - self.health
					self.Game.CounterHandler.healthRestoredThisGame[subject.ID] += healDone
					self.health = self.health_upper
					if sendHealSignal: #During AOE healing, the signals are delayed.
						self.Game.sendSignal("MinionGetsHealed", self.Game.turn, subject, self, heal, "FullyHealed")
					for func in self.triggers["StatChanges"]:
						func()
					return healDone, -2
		else: #If the minion is dead and removed already or in deck. Nothing happens.
			return 0, 0
			
	def deathResolution(self, attackbeforeDeath, triggersAllowed_WhenDies, triggersAllowed_AfterDied):
		print("Now resolving the death of ", self.name)
		self.Game.sendSignal("MinionDies", self.Game.turn, None, self, attackbeforeDeath, "", 0, triggersAllowed_WhenDies)
		#随从的亡语也需要扳机化，因为亡语和“每当你的一个xx随从死亡”的扳机的触发顺序也由其登场顺序决定
		#如果一个随从有多个亡语（后来获得的，那么土狼会在两个亡语结算之间触发。所以说这些亡语是严格意义上的扳机）
		#随从入场时注册亡语扳机，除非注明了是要结算死亡的情况下，disappears()的时候不会直接取消这些扳机，而是等到deathResolution的时候触发这些扳机
		#如果是提前离场，如改变控制权或者是返回手牌，则需要取消这些扳机
		#扳机应该注册为场上扳机，这个扳机应该写一个特殊的类，从而使其可以两次触发，同时这个类必须可存储一个attribute,复制效果可以复制食肉魔块等战吼提供的信息
		#区域移动类扳机一般不能触发两次
		#触发扳机如果随从已经不在场上，则说明它区域移动然后进入了牌库或者手牌。同类的区域移动扳机不会触发。
		#区域移动的死亡扳机大多是伪区域移动，实际上是将原实体移除之后将一个复制置入相应区域。可以通过魔网操纵者来验证。只有莫里甘博士和阿努巴拉克的亡语是真的区域移动
		#鼬鼠挖掘工的洗入对方牌库扳机十分特别，在此不予考虑，直接视为将自己移除，然后给对方牌库里洗入一个复制
		#The minion resets its own status. But it will record its current location.
		#If returned to hand/deck already due to deathrattle, the inHand/inDeck will be kept
		#假设随从只有在场上结算亡语完毕之后才会进行初始化，而如果扳机已经提前将随从返回手牌或者牌库，则这些随从不会
		#移除随从注册了的亡语扳机
		for trigger in self.deathrattles:
			trigger.disconnect()
		if self in self.Game.minions[self.ID]:
			self.__init__(self.Game, self.ID)
		self.Game.sendSignal("MinionDied", self.Game.turn, None, self, 0, "", 0, triggersAllowed_AfterDied)
		#MinionDeathResolutionFinished
		
	def selectablebySpellandHeroPower(self, subject):
		if self.onBoard and self.marks["Evasive"] == False:
			if self.ID == subject.ID:
				return True
			else:
				if self.marks["Enemy Evasive"] + self.status["Immune"] + self.keyWords["Stealth"] + self.status["Temp Stealth"] < 1:
					return True
		return False
		
	def selectablebyBattlecry(self, subject):
		if self.onBoard:
			if self.ID == subject.ID:
				return True
			else:
				if self.status["Immune"] + self.keyWords["Stealth"] + self.status["Temp Stealth"] < 1:
					return True
		return False
		
	def selectablebyBattle(self, subject):
		if self.onBoard and self.ID != subject.ID and self.status["Temp Stealth"] + self.status["Immune"] + self.keyWords["Stealth"] < 1:
			if self.keyWords["Taunt"] > 0:
				return True
			else:
				for minion in self.Game.minionsonBoard(self.ID):
					if minion.keyWords["Taunt"] > 0 and minion.selectablebyBattle(subject):
						print(self.name, " is behind friendly Taunt minions and can't be attacked first.")
						return False
				return True
		print(self.name, " is a friendly or has Stealth or Immune.")
		return False
		
	def magnetCombine(self, target):
	#暂时假设磁力随从如果死亡则不触发磁力。
	#先将随从从场上或者手牌中移除。
		if self.onBoard:
			#磁力随从因为磁力触发离场时会注销其已经注册的死亡扳机，最终会将这些死亡扳机赋予磁力目标
			self.disappears(keepDeathrattlesRegistered=False)
			self.Game.removeMinionorWeapon(self)
		else: #The Magnetic minion is inHand
			self.Game.Hand_Deck.extractfromHand(self)
			
		#在打出磁力随从时，需要得知其原有的关键字、身材和扳机等，需要进行复制，然后录入随从的磁力升级历史
		Copy = self.selfCopy(self.ID) #Find the original keywords the minion has
		attack_orig, health_orig = Copy.attack_Enchant, Copy.health
		keyWords_orig, marks_orig = {}, {}
		for key, value in Copy.keyWords.items():
			if value > 0:
				keyWords_orig[key] = value
		#暂时假设磁力随从不会保留状态，如临时潜行和冰冻
		for key, value in Copy.marks.items():
			if value > 0:
				marks_orig[key] = value
		#将随从携带的扳机也记录,磁力随从是没有手牌扳机和场上扳机的
		triggers_orig, deathrattles_orig = [], []
		for trigger in Copy.triggersonBoard:
			if trigger.temp == False: #临时扳机不会被记录和赋予，如腐蚀术
				triggers_orig.append(type(trigger))
		for trigger in Copy.deathrattles:
			deathrattles_orig.append(type(trigger))
		#磁力随从没有triggers[]的方法，如激怒等
		#将关键字赋予随从
		for key, value in keyWords_orig.items():
			for i in range(value):
				target.getsKeyword(key)
				if key in target.history["Magnetic Upgrades"]["Keywords"].keys():
					target.history["Magnetic Upgrades"]["Keywords"][key] += value
				else: #如果这个关键字是之前没有的，则在dict里面添加这个key
					target.history["Magnetic Upgrades"]["Keywords"][key] = value
		#将类关键字赋予随从
		for key, value in marks_orig.items():
			target.marks[key] += value
			if key in target.history["Magnetic Upgrades"]["Marks"].keys():
				target.history["Magnetic Upgrades"]["Marks"][key] += value
			else:
				target.history["Magnetic Upgrades"]["Marks"][key] = value
		#将扳机赋予随从，同时记录在目标随从的"Magnetic Upgrades"中
		for trigger_Class in deathrattles_orig:
			trigger = trigger_Class(target)
			target.deathrattles.append(trigger)
			trigger.connect()
			target.history["Magnetic Upgrades"]["Deathrattles"].append(trigger_Class)
		#将亡语赋予随从，同时记录在"Magnetic Upgrades"里面
		for trigger_Class in triggers_orig:
			trigger = trigger_Class(target)
			target.triggersonBoard.append(trigger)
			trigger.connect()
			target.history["Magnetic Upgrades"]["Triggers"].append(trigger_Class)
		#最后进行身材的改变，并在这里调用目标随从的StatChanges方法
		target.buffDebuff(attack_orig, health_orig)
		target.history["Magnetic Upgrades"]["AttackGain"] += attack_orig
		target.history["Magnetic Upgrades"]["HealthGain"] += health_orig
		self.Game.minionPlayed = None
		
	#Specifically for battlecry resolution. Doesn't care if the target is in Stealth.
	def targetCorrect(self, target, choice=0):
		if target.cardType != "Minion" and target.cardType != "Hero":
			print("Target is not minion or hero.")
			return False
		if target.onBoard == False:
			print("Target is not on board.")
			return False
		if target == self:
			print("Minion can't select self.")
			return False
		return True
		
	#Minions that initiates discover or transforms self will be different.
	#For minion that transform before arriving on board, there's no need in setting its onBoard to be True.
	#By the time this triggers, death resolution caused by Illidan/Juggler has been finished. 
	#If Brann Bronzebeard/ Mayor Noggenfogger has been killed at this point, they won't further affect the battlecry.
	def played(self, target=None, choice=0, mana=0, comment=""):
		#即使该随从在手牌中的生命值为0或以下，打出时仍会重置为无伤状态。
		self.statReset(self.attack_Enchant, self.health_Enchant)
		#此时，随从可以开始建立光环，建立侦听，同时接受其他光环。例如： 打出暴风城勇士之后，光环在Illidan的召唤之前给随从加buff，同时之后打出的随从也是先接受光环再触发Illidan。
		self.appears()
	#使用阶段
		#使用时步骤,触发“每当你使用一张xx牌”的扳机,如伊利丹，任务达人，无羁元素和魔能机甲等
			#触发信号依次得到主玩家的场上，手牌和牌库的侦听器的响应，之后是副玩家的侦听器响应。
			#伊利丹可以在此时插入召唤和飞刀的结算，之后在战吼结算开始前进行死亡的判定，同时subject和target的位置情况会影响战吼结果。
		self.Game.sendSignal("MinionPlayed", self.ID, self, target, mana, "", choice)
		#召唤时步骤，触发“每当你召唤一个xx随从”的扳机.如鱼人招潮者等。
		self.Game.sendSignal("MinionSummoned", self.ID, self, target, mana, "")
		#过载结算
		if self.overload > 0:
			print(self.name, " is played and Overloads %d mana crystals."%self.overload)
			self.Game.ManaHandler.overloadMana(self.overload, self.ID)
			
		magneticTarget = None
		if self.magnetic > 0:
			if self.onBoard:
				adjacentMinions, distribution = self.Game.findAdjacentMinions(self)
				if distribution == "Minions on Both Sides" and "Mech" in adjacentMinions[1].race:
					magneticTarget = adjacentMinions[1]
				elif distribution == "Minions Only on the Right" and "Mech" in adjacentMinions[0].race:
					magneticTarget = adjacentMinions[0]
		#使用阶段结束，开始死亡结算。视随从的存活情况决定战吼的触发情况，此时暂不处理胜负问题。
		self.Game.gathertheDead() #At this point, the minion might be removed/controlled by Illidan/Juggler combo.		
	#结算阶段
		if self.magnetic > 0:
			#磁力相当于伪指向性战吼，一旦指定目标之后，不会被其他扳机改变
			#磁力随从需要目标和自己都属于同一方,且磁力目标在场时才能触发。
			if magneticTarget != None and magneticTarget.onBoard and self.ID == magneticTarget.ID:
				#磁力结算会让随从离场，不会触发后续的随从召唤后，打出后的扳机
				self.magnetCombine(magneticTarget)
				#磁力随从没有战吼等入场特效，因而磁力结算不会引发死亡，不必进行死亡结算
		else: #无磁力的随从
			#市长会在战吼触发前检测目标，指向性战吼会被随机取向。一旦这个随机过程完成，之后的第二次战吼会重复对此目标施放。
			#如果场上有随从可供战吼选择，但是因为免疫和潜行导致打出随从时没有目标，则不会触发随机选择，因为本来就没有目标。
			#在战吼开始检测之前，如果铜须已经死亡，则其并不会让战吼触发两次。也就是扳机的机制。
			#同理，如果此时市长已经死亡，则其让选择随机化的扳机也已经离场，所以不会触发随机目标。
			if target != None:
				targetHolder = [target]
				self.Game.sendSignal("MinionBattlecryTargetSelected", self.ID, self, targetHolder, 0, "", choice)
				target = targetHolder[0]
			#市长不会让发现和抉择选项的选择随机化。
			#不管target是否还在场上，此时只要市长还在，就要重新在场上寻找合法目标。如果找不到，就不能触发战吼的指向性部分，以及其产生的后续操作。
			#随机条件下，如果所有合法目标均已经消失，则return None. 由随从的战吼决定是否继续生效。
			
			#在随从战吼/连击开始触发前，检测是否有战吼/连击翻倍的情况。如果有且战吼可以进行，则强行执行战吼至两次循环结束。无论那个随从是死亡，在手牌中还是牌库
			num = 1
			if "-Battlecry" in self.index and self.Game.playerStatus[self.ID]["Battlecry Trigger Twice"] + self.Game.playerStatus[self.ID]["Shark Battlecry Trigger Twice"] > 0:
				num = 2
			if "-Combo" in self.index and self.Game.playerStatus[self.ID]["Shark Battlecry Trigger Twice"] > 0:
				num = 2
				#不同的随从会根据目标和自己的位置和状态来决定effectwhenPlayed()产生体积效果。
				#可以变形的随从，如无面操纵者，会有自己的played（） 方法。 大王同理。
				#战吼随从自己不会进入牌库，因为目前没有亡语等效果可以把随从返回牌库。
				#发现随从如果在战吼触发前被对方控制，则不会引起发现，因为炉石没有对方回合外进行操作的可能。
				#结算战吼，连击，抉择
			for i in range(num):
				target = self.whenEffective(target, "", choice)
				
			#结算阶段结束，处理死亡情况，不处理胜负问题。
			self.Game.gathertheDead()
		return target
		
	def countHealDouble(self):
		num = 0
		for minion in self.Game.minionsonBoard(self.ID):
			if minion.marks["Double Heal"] > 0:
				num += 1
		return num
		
	"""buffAura effect, Buff/Debuff, stat reset, copy"""
	#Generally invoked by buffAura_Receivers and buffDebuff.
	def statChange(self, attackChange, healthChange):
		self.attack += attackChange
		if healthChange >= 0:
			self.health += healthChange
			self.health_upper += healthChange
		else: #When the buffAura is gone.
			self.health_upper += healthChange
			self.health_upper = max(1, self.health_upper)
			if self.health > self.health_upper:
				self.health = self.health_upper
		for func in self.triggers["StatChanges"]:
			func()
			
	#attChangeDisappearTime = "' or "EndofTurn" or "StartofTurn 1" or "StartofTurn 2"
	def buffDebuff(self, attackGain, healthGain, attChangeDisappearTime=''):
		if self.inDeck == False: #只有随从在场上或者手牌中的时候可以接受buff。
			self.health_Enchant += healthGain #By default, this healthGain has to be non-negative.
			if attChangeDisappearTime == "": #在场上和手牌中都可以接受永久buff
				self.statChange(attackGain, healthGain)
				self.attack_Enchant += attackGain
			else: #Minions can receive temp attack changes, too. And those will also vanish at the corresponding time point.
				self.statChange(attackGain, healthGain)
				self.tempAttackChanges.append((attackGain, attChangeDisappearTime))
				
	#Not all params can be False.
	def statReset(self, newAttack=False, newHealth=False):
		CurrentBuffAura_Receivers = fixedList(self.stat_AuraAffected[2])
		#将随从上的全部buffAura清除，因为部分光环的适用条件可能会因为随从被沉默而变化，如战歌指挥官
		for buffAura_Receiver in CurrentBuffAura_Receivers:
			buffAura_Receiver.effectClear()
			
		if newAttack != False: #The minion's health is reset.
			self.attack, self.attack_Enchant = newAttack, newAttack
			self.tempAttackChanges = [] #Clear the temp attack changes on the minion.
		if newHealth != False:
			self.health, self.health_upper, self.health_Enchant = newHealth, newHealth, newHealth
			
		#清除全部buffAura并重置随从的生命值之后，让原来的buffAura_Dealer自行决定是否重新对该随从施加光环。
		for buffAura_Receiver in CurrentBuffAura_Receivers:
			buffAura_Receiver.source.applies(self)
		for func in self.triggers["StatChanges"]:
			func()
			
	def selfCopy(self, ID, attack=False, health=False, mana=False):
		Copy = type(self)(self.Game, ID)
		for key, value in self.__dict__.items():
			#print("Now copying minion's attribute", key, value)
			#Copy the attributes of basic types.
			if isinstance(value, (type(None), int, np.int64, float, str, bool)):
				Copy.__dict__[key] = value
			#随从实例上带有的函数一经__init__确定不会改变。所以不需要进行复制
			elif callable(value): #If the attribute is a function
				pass
			#用于auras，stat_AuraAffected，keyWords_AuraAffected和manaModifications等
			elif type(value) == list or type(value) == dict: #If the attribute is a list or dictionary, use the method defined at the start of py
				Copy.__dict__[key] = copyListDict(value, Copy)
			elif type(value) == type(self.Game): #Only shallow copies the Game.
				Copy.__dict__[key] = self.Game
			else: #The attribute is a self-defined class. They will all have selfCopy methods
				#A minion can't refernece another minion. The attributes here must be like triggers/deathrattles	
				Copy.__dict__[key] = value.selfCopy(Copy)
				
		Copy.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		Copy.Game, Copy.ID = self.Game, ID
		#随从的光环和亡语复制完全由各自的selfCopy函数负责。
		for aura_Receiver in Copy.stat_AuraAffected[2]:
			aura_Receiver.effectDiscard()
		for aura_Receiver in Copy.keyWords_AuraAffected["Auras"]:
			aura_Receiver.effectDiscard()
		Copy.activated = False
		#如果要生成一个x/x/x的复制
		if attack != False or health != False:
			Copy.statReset(attack, health)
		for manaMod in Copy.manaModifications:
			manaMod.activated = False
		if mana != False:
			for manaMod in Copy.manaModifications:
				manaMod.getsRemoved()
			Copy.manaModifications = []
			ManaModification(Copy, changeby=0, changeto=mana)
		return Copy
		
	##在复制一个随从的时候只会复制其身材的非光环部分。包括额外效果和暂时的攻击力增加。
	##复制随从所有的全部扳机, 全部光环, 去掉光环的身材, 全部triggers方法。
	#def selfCopy(self, ID, attack=False, health=False, mana=False):
	#	Copy = copy.deepcopy(self)
	#	Copy.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
	#	Copy.Game, Copy.ID = self.Game, ID
	#	#随从的亡语在被复制的时候也要调用其专有的函数，诸如巫毒娃娃这样的亡语需要考虑其标记的随从，不能任由copy.deepcopy更改
	#	Copy.deathrattles = [] #此时复制来的亡语还没有被注册，可以直接清除
	#	for trigger in self.deathrattles:
	#		Copy.deathrattles.append(trigger.selfCopy(Copy))
	#	#Any buffAura or hasAura affecting the copied minion won't be replicated.
	#	#随从的攻击力和生命都承袭原随从，但是需要去掉原随从因为光环而得到的数值。
	#	#随从攻击力的暂时部分已经被copy在其tempAttackChanges列表中了，会在与原随从相同的时间点消失。
	#	for aura_Receiver in Copy.stat_AuraAffected[2]:
	#		aura_Receiver.effectDiscard()
	#	#随从因为关键字光环获得的buff也要清除。
	#	for aura_Receiver in Copy.keyWords_AuraAffected["Auras"]:
	#		aura_Receiver.effectDiscard()
	#	#随从携带的扳机以及亡语在复制过程中，其entity会和随从本身一同被复制，但是不会直接注册在所属的Game的triggersonBoard中，需要在入场时重新注册
	#	#Remove the objects in the copy's own aura_Dealers.
	#	for aura_Dealer in Copy.auras.values():
	#		aura_Dealer.auraAffected = [] #光环中所记录的(随从与receiver)都已经被复制成不存在目标，需要清除。
	#	#南海船工之类，除了扳机之外，还有appearResponse，复制之后没有问题。无需特殊处理。
	#	#该标志用于激怒和圣光楷模等自身状态改变的标识。在复制时将其重置为False，之后随从召唤时根据情况重新启动
	#	Copy.activated = False
	#	
	#	#Make a copy with specified stat.
	#	if attack != False or health != False:
	#		Copy.statReset(attack, health)
	#	#If the card is added from board to hand, the mana is equal to its original mana cost.
	#	#Appear function will take care of reset onBoard minions' mana to original.
	#	
	#	#当一张牌在手牌中被复制时，如果处理其受到的光环效果和费用修改效果会如何？
	#		#假设其像身材一样，复制时不会复制费用光环的影响。
	#	#当一张牌被复制时，其费用修改效果会被复制，但是需要把那些被标记为激活状态的效果手动调至关闭状态。
	#	for manaMod in Copy.manaModifications:
	#		manaMod.activated = False
	#	if mana != False:
	#		for manaMod in Copy.manaModifications:
	#			manaMod.getsRemoved()
	#		Copy.manaModifications = []
	#		ManaModification(Copy, changeby=0, changeto=mana)
	#	return Copy
		
	#破法者因为阿努巴尔潜伏者的亡语被返回手牌，之后被沉默，但是仍然可以触发其战吼
	#在手牌中时不能接受沉默。已经用紫罗兰老师测试过了，仍然可以触发其扳机，没有沉默标记
	def getsSilenced(self):
		if self.onBoard:
			self.silenced, self.activated = True, True
			#随从如需对沉默做出响应，在此处理。然后移除被沉默，出场，离场的特殊响应
			for func in self.silenceResponse:
				func()
			self.silenceResponse, self.appearResponse, self.disappearResponse = [], [], []
			#Remove the enrage/Lightspawn effects. And discard effect.
			for value in self.triggers.values():
				value = []
			#Shut down minion's auras, if any. And clear them
			for key, value in self.auras.items():
				value.auraDisappears()
				
			self.auras = {}
			#清除所有场上扳机,亡语扳机，手牌扳机和牌库扳机。然后将这些扳机全部清除	
			for trigger in self.triggersonBoard + self.deathrattles + self.triggersinHand + self.triggersinDeck:
				trigger.disconnect()
			self.triggersonBoard, self.deathrattles, self.triggersinHand, self.triggersinDeck = [], [], [], []
			#清除随从因为关键字光环获得的关键字：冲锋，突袭，超级风怒。这些关键字是否之后恢复由光环施加者决定。
			#暂时不清除随从身上的buffAura增益，统一留到最后的statReset()中处理。
			CurrentKeywordAura_Receivers = fixedList(self.keyWords_AuraAffected["Auras"])
			for keywordAura_Receiver in CurrentKeywordAura_Receivers:
				keywordAura_Receiver.effectClear()
			#清除随从身上的所有原有关键字。
			for key, value in self.keyWords.items():
				if value > 0:
					value = 1
					self.losesKeyword(key)
				value = 0
			#清除随从身上的所有原有状态。
			for key, value in self.status.items():
				#If Temp Controlled when silenced, return it to the other side.
				#The minion only remember one Temp Controlled state, even if repetitively moved between two sides.
				if key == "Temp Controlled" and value > 0:
					self.Game.minionSwitchSide(self, activity="Return")
				value = 0
			#清除随从身上的历史记录，主要为对该随从施放的法术和机械随从的磁力叠加历史。
			for value in self.history.values():
				value = []
			#随从被沉默不发出沉默信号，所有接受的keywordAura就地处理。
			for keywordAura_Receiver in CurrentKeywordAura_Receivers:
				keywordAura_Receiver.source.applies(self)
			self.decideAttChances_base()
			#self.statReset() can handle stat_AuraAffected
			#沉默后的血量计算是求当前血量上限与实际血量的差，沉默后在基础血量上扣除该差值。（血量不能小于1）
			damageTaken = self.health_upper - self.health
			#在此处理随从身上存在的buffAura的效果。先是将其全部取消，然后看之前的光环是否还会继续对其产生作用。
			self.statReset(self.attack_0, self.health_0)
			self.health -= damageTaken
			self.health = max(1, self.health)
			
			
			
class Spell(Card):
	Class, name = "Neutral", "Test"
	needTarget, mana = False, 2
	index = "None-1-Spell-Test"
	description = ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.Class, self.name = type(self).Class, type(self).name
		self.cardType = "Spell"
		self.index = type(self).index
		self.mana, self.manaModifications = type(self).mana, []
		self.needTarget = self.returnTrue if type(self).needTarget else self.returnFalse
		self.description = type(self).description
		self.overload, self.chooseOne, self.twinSpell = 0, 0, 0
		#法术也设置onBoard标签，但只是placeholder而已
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		#法术的triggersonBoard只是一个placeholder
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.options = [] #For Choose One spells
		self.keyWords = {"Poisonous": 0, "Lifesteal": 0}
		self.triggers = {"Discarded": []}
		self.effectViable, self.evanescent = False, False
		
	def statusPrint(self):
		print("Spell: %s. Description:"%self.name, self.description)
		#print("Spell inHand: ", self.inHand, " inDeck:", self.inDeck)
		if self.triggersinHand != []:
			print("Spell's triggersinHand")
			for trigger in self.triggersinHand:
				print(type(trigger))
		#if self.triggersinDeck != []:
		#	print("Spell's triggersinDeck")
		#	for trigger in self.triggersinDeck:
		#		print(type(trigger))
		#		
	"""Handle the card being selected and check the validity of selection and target."""
	def available(self):
		if self.needTarget():
			return self.selectableCharacterExists()
		return True
		
	def selectableFriendlyExists(self, choice=0):
		if self.Game.heroes[self.ID].selectablebySpellandHeroPower(self) and self.targetCorrect(self.Game.heroes[self.ID], choice):
			return True
		return self.selectableFriendlyMinionExists(choice)
		
	"""Handle the spell being played by player and cast by other cards."""
	#用于由其他卡牌释放法术。这个法术会受到风潮和星界密使的状态影响，同时在结算完成后移除两者的状态。
	#这个由其他卡牌释放的法术不受泽蒂摩的光环影响。
	#目标随机，也不触发目标扳机。
	def cast(self, target=None, comment="CastbyOthers"):
		#由其他卡牌释放的法术结算相对玩家打出要简单，只需要结算过载，双生法术， 重复释放和使用后的扳机步骤即可。
		#因为这个法术是由其他序列产生的，所有结束时不会进行死亡处理。
		repeatTimes = 2 if self.Game.playerStatus[self.ID]["Spells Cast Twice"] > 0 else 1
		#多次选择的法术，如分岔路口等会有自己专有的cast方法。
		if self.chooseOne > 0:
			if self.Game.playerStatus[self.ID]["Choose Both"]:
				choice = "ChooseBoth"
			else:
				choice = np.random.randint(len(self.options))
		else:
			choice = 0
		#如果法术需要目标，而target已经指定，则遵照已经指定的target进行结算。目前只有沼泽女王哈加莎的恐魔会如此结算。
		if self.needTarget(choice) and target == None:
			targets = self.returnTargets("IgnoreStealthandImmune", choice)
			if targets != []:
				target = np.random.choice(targets)
				print(self.name, " gets a random target ", target.name)
			else:
				print("Targeting spell %s has no available target."%self.name)
				target = None
		else:
			print(self.name, " is non-targeting.")
			target = None
		#在法术要施放两次的情况下，第二次的目标仍然是第一次时随机决定的
		for i in range(repeatTimes):
			if self.overload > 0:
				print(self.name, " is cast and Overloads %d mana crystals."%self.overload)
				self.Game.ManaHandler.overloadMana(self.overload, self.ID)
			if self.twinSpell > 0:
				print("Twinspell", self.name, "is cast and adds a another copy to player's hand")
				self.Game.Hand_Deck.addCardtoHand(self.twinSpellCopy, self.ID, "CreateUsingType")
			#指向性法术如果没有目标也可以释放，只是可能没有效果而已
			target = self.whenEffective(target, "CastbyOthers", choice)
		#使用后步骤，但是此时的扳机只会触发星界密使和风潮的状态移除。这个信号不是“使用一张xx牌之后”的扳机。
		self.Game.sendSignal("SpellBeenCast", self.ID, self, target, 0, "CastbyOthers", choice=0)
		
	#泽蒂摩加风潮，当对泽蒂摩使用Mutate之后，Mutate会连续两次都进化3个随从
	#泽蒂摩是在法术开始结算之前打上标记,而非在连续两次之间进行判定。
	#comment = "InvokedbyAI", "Branching-i", ""
	def played(self, target=None, choice=0, mana=0, comment=""):
		#使用阶段
		#判定该法术是否会因为风潮的光环存在而释放两次。发现的子游戏中不会两次触发，直接跳过
		if "Branching" not in comment:
			repeatTimes = 2 if self.Game.playerStatus[self.ID]["Spells Cast Twice"] > 0 else 1
		#使用时步骤，触发伊利丹和紫罗兰老师等“每当你使用一张xx牌”的扳机
		self.Game.sendSignal("SpellPlayed", self.ID, self, target, mana, "", choice)
		#获得过载和双生法术牌。
		if self.overload > 0:
			print(self.name, "is cast and Overloads %d mana crystals."%self.overload)
			self.Game.ManaHandler.overloadMana(self.overload, self.ID)
		if self.twinSpell > 0:
			print("Twinspell", self.name, "is cast and adds a another copy to player's hand")
			self.Game.Hand_Deck.addCardtoHand(self.twinSpellCopy, self.ID, "CreateUsingType")
			
		#使用阶段结束，进行死亡结算。不处理胜负裁定。
		self.Game.gathertheDead() #At this point, the minion might be removed/controlled by Illidan/Juggler combo.		
		#进行目标的随机选择和扰咒术的目标改向判定。
		targetHolder = [target]
		self.Game.sendSignal("SpellTargetDecision", self.ID, self, targetHolder, 0, choice)
		target = targetHolder[0]
		#Zentimo's effect actually an aura. As long as it's onBoard the moment the spell starts being resolved, 
		#the effect will last even if Zentimo leaves board early.
		targetAdjacentMinions = self.Game.playerStatus[self.ID]["Spells Target Adjacent Minions"]
		#没有法术目标，且法术本身是点了需要目标的选项的抉择法术或者需要目标的普通法术。
		for i in range(repeatTimes):
			if i == 1: #第二次施放时照常获得过载和双生法术牌。
				if self.overload > 0:
					print(self.name, " is played and Overloads %d mana crystals."%self.overload)
					self.Game.ManaHandler.overloadMana(self.overload, self.ID)
				if self.twinSpell > 0:
					print("Twinspell", self.name, "is cast and adds a another copy to player's hand")
					self.Game.Hand_Deck.addCardtoHand(self.twinSpellCopy, self.ID, "CreateUsingType")
					
			print("The target for the spell is now ", target)
			#When the target is an onBoard minion, Zentimo is still onBoard and has adjacent minions next to it.
			if target != None and target.cardType == "Minion" and target.onBoard and targetAdjacentMinions > 0 and self.Game.findAdjacentMinions(target)[0] != []:
				targets = self.Game.findAdjacentMinions(target)[0]
				#只对中间的目标随从返回法术释放之后的新目标。
				#用于变形等会让随从提前离场的法术。需要知道后面的再次生效目标。
				target.history["Spells Cast on This"].append(self.index)
				target = self.whenEffective(target, comment, choice)
				print(self.name, " will also be cast upon minions", targets, " adjacent to the target ", target.name, " with choice", choice)
				for minion in targets: #对相邻的随从也释放该法术。
					minion.history["Spells Cast on This"].append(self.index)
					self.whenEffective(minion, comment, choice)
			else: #The target isn't minion or Zentimo can't apply to the situation. Be the target hero, minion onBoard or inDeck or None.
				#如果目标不为空而且是在场上的随从，则这个随从的历史记录中会添加此法术的index。
				if target != None and target.cardType == "Minion" and target.onBoard:
					target.history["Spells Cast on This"].append(self.index)
					
				target = self.whenEffective(target, comment, choice)
				
		#仅触发风潮，星界密使等的光环移除扳机。“使用一张xx牌之后”的扳机不在这里触发，而是在Game的playSpell函数中结算。
		self.Game.sendSignal("SpellBeenCast", self.Game.turn, self, target, 0, "", choice)
		#使用阶段结束，进行死亡结算，暂不处理胜负裁定。
		self.Game.gathertheDead() #At this point, the minion might be removed/controlled by Illidan/Juggler combo.		
		
	#完成阶段：
		#如果法术具有回响，则将回响牌置入手牌中。因为没有牌可以让法术获得回响，所以可以直接在法术played()方法中处理echo
		if "-Echo" in self.index:
			echoCard = type(minion)(self, self.Game.turn)
			trigger = Trigger_Echo(echoCard)
			echoCard.triggersinHand.append(trigger)
			self.Game.Hand_Deck.addCardtoHand(echoCard, self.ID)
			
	def whenEffective(self, target=None, comment="", choice=0):
		return target
		
	def afterDrawingCard(self):
		pass
	"""Handle the spell dealing damage and restoring health."""
	def countSpellDamage(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			num += minion.keyWords["Spell Damage"]
		num += self.Game.playerStatus[self.ID]["Spell Damage"]
		return num
		
	def countDamageDouble(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			if minion.marks["Spell Double Heal and Damage"] > 0:
				num += 1
		return num
		
	def countHealDouble(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			if minion.marks["Double Heal"] > 0 or minion.marks["Spell Double Heal and Damage"] > 0:
				num += 1
		return num
		
		
		
class Secret(Spell):
	Class, name = "Neutral", "Vanilla"
	needTarget, mana = False, 1
	index = "Neutral~1~Spell~Vanilla~~Secret"
	description = ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Class = type(self).Class
		self.name = type(self).name
		self.index = type(self).index
		self.mana, self.manaModifications = type(self).mana, []
		self.Game, self.ID = Game, ID
		self.needTarget = self.returnTrue if type(self).needTarget else self.returnFalse
		self.cardType = "Spell"
		self.description = type(self).description
		self.overload, self.chooseOne, self.twinSpell = 0, 0, 0
		#法术也设置onBoard标签，但只是placeholder而已
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.identity = [np.random.rand(), np.random.rand()]
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.options = [] #For Choose One spells
		self.keyWords = {"Poisonous": 0, "Lifesteal": 0}
		self.evanescent = False
		
	def available(self):
		if self.Game.SecretHandler.areaNotFull(self.ID):
			return self.Game.SecretHandler.isSecretDeployedAlready(self, self.ID) == False
		return False
		
	def selectionLegit(self, target, choice=0):
		return target == None
		
	def cast(self, target=None, comment="CastbyOthers"):
		#指向性法术如果没有目标也可以释放，只是可能没有效果而已
		self.whenEffective(None, "CastbyOthers", choice=0)
		#使用后步骤，但是此时的扳机只会触发星界密使和风潮的状态移除，因为其他的使用后步骤都要求是玩家亲自打出。
		self.Game.sendSignal("SpellBeenCast", self.ID, self, None, 0, "CastbyOthers")
		
	def played(self, target=None, choice=0, mana=0, comment=""):
		self.Game.sendSignal("SpellPlayed", self.ID, self, None, mana, "", choice)
		self.Game.gathertheDead() #At this point, the minion might be removed/controlled by Illidan/Juggler combo.		
		self.whenEffective(None, '', choice)
		#There is no need for another round of death resolution.
		self.Game.sendSignal("SpellBeenCast", self.ID, self, None, 0, "")
		
	def whenEffective(self, target=None, comment="", choice=0):
		secretcanRegister = True
		if self.Game.SecretHandler.areaNotFull(self.ID) and self.Game.SecretHandler.isSecretDeployedAlready(self, self.ID) == False:
			self.Game.SecretHandler.secrets[self.ID].append(self)
			for trigger in self.triggersonBoard:
				trigger.connect() #把(obj, signal)放入Game.triggersonBoard中
		else:
			secretcanRegister = False
		if secretcanRegister == False:
			print("Secret %s cannot register due to full area or existing same kind of secret"%self.name)
		return None
		
		
		
class Quest(Spell):
	Class, name = "Neutral", "Vanilla"
	needTarget, mana = False, 1
	index = "Neutral-1-Spell-Vanilla--Quest"
	description = ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.Class, self.name = type(self).Class, type(self).name
		self.cardType = "Spell"
		self.index = type(self).index
		self.mana, self.manaModifications = type(self).mana, []
		self.needTarget = self.returnTrue if type(self).needTarget else self.returnFalse
		self.description = type(self).description
		self.overload, self.chooseOne, self.twinSpell = 0, 0, 0
		#法术也设置onBoard标签，但只是placeholder而已
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.identity = [np.random.rand(), np.random.rand()]
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.options = [] #For Choose One spells
		self.keyWords = {"Poisonous": 0, "Lifesteal": 0}
		self.progress = 0
		self.evanescent = False
		
	def available(self):
		if self.Game.SecretHandler.areaNotFull(self.ID):
			if self.description.startswith("Sidequest"):
				for quest in self.Game.SecretHandler.sideQuests[self.ID]:
					if quest.name == self.name: #Sidequests can coexist with other different quest and Sidequests
						return False
			else: #If the subject is a main quest. Then there can only be only main quest
				if self.Game.SecretHandler.mainQuests[self.ID] != []: #Sidequests can coexist with other different quest and sidequests
					return False
			return True #If the there are no same kind of quests in the way, return True
		return False
		
	def selectionLegit(self, target, choice=0):
		return target == None
		
	def cast(self, target=None, comment="CastbyOthers"):
		#指向性法术如果没有目标也可以释放，只是可能没有效果而已
		self.whenEffective(None, "CastbyOthers", choice=0)
		#使用后步骤，但是此时的扳机只会触发星界密使和风潮的状态移除，因为其他的使用后步骤都要求是玩家亲自打出。
		self.Game.sendSignal("SpellBeenCast", self.ID, self, None, 0, "CastbyOthers")
		
	def played(self, target=None, choice=0, mana=0, comment=""):
		self.Game.sendSignal("SpellPlayed", self.ID, self, None, mana, "", choice)
		self.Game.gathertheDead() #At this point, the minion might be removed/controlled by Illidan/Juggler combo.		
		self.whenEffective(None, '', choice)
		#There is no need for another round of death resolution.
		self.Game.sendSignal("SpellBeenCast", self.ID, self, None, 0, "")
		
	def whenEffective(self, target=None, comment="", choice=0):
		questcanRegister = True
		if self.Game.SecretHandler.areaNotFull(self.ID):
			if self.description.startswith("Sidequest"):
				for quest in self.Game.SecretHandler.sideQuests[self.ID]:
					if quest.name == self.name:
						questcanRegister = False
						break
				if questcanRegister:
					self.Game.SecretHandler.sideQuests[self.ID].append(self)
					for trigger in self.triggersonBoard:
						trigger.connect()
			else: #The quest is a main quest	
				if self.Game.SecretHandler.mainQuests[self.ID] == []:
					self.Game.SecretHandler.mainQuests[self.ID].append(self)
					for trigger in self.triggersonBoard:
						trigger.connect() #把(obj, signal)放入Game.triggersonBoard中
				else:
					questcanRegister = False
		else:
			questcanRegister = False
		if questcanRegister == False:
			print("Quest %s cannot register due to full area or existing same kind of quest"%self.name)
		return None
		
		
		
class HeroPower(Card):
	name, needTarget = "Test", False
	index = "Neutral-2-Hero Power-Vanilla"
	description = ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.name = type(self).name
		self.cardType = "Hero Power"
		self.description = type(self).description
		self.heroPowerTimes = 0
		#额外的英雄技能技能只有考达拉幼龙和要塞指挥官可以更改。
		#技能能否使用，需要根据已使用次数和基础机会和额外机会的和相比较。
		self.heroPowerChances_base, self.heroPowerChances_extra = 1, 0
		self.mana, self.manaModifications = 2, []
		self.needTarget = self.returnTrue if type(self).needTarget else self.returnFalse
		self.chooseOne = 0
		self.options = [] #For Choose One
		self.keyWords = {"Lifesteal": 0,
						"Poisonous": 0 #As a placeholder
						}
		self.triggersonBoard = []
		
	def statusPrint(self):
		print("Hero Power: %s. Description:"%self.name, self.description)
		print("Chances to use_base: %d. Chances to use_extra"%self.heroPowerChances_base, self.heroPowerChances_extra)
		
	def turnStarts(self, ID):
		if ID == self.ID:
			self.heroPowerChances_base, self.heroPowerChances_extra = 1, 0
			self.heroPowerTimes = 0
			
	def turnEnds(self, ID):
		if ID == self.ID:
			self.heroPowerChances_base, self.heroPowerChances_extra = 1, 0
			self.heroPowerTimes = 0
			
	def appears(self):
		self.heroPowerChances = 1
		self.heroPowerTimes = 0
		for trigger in self.triggersonBoard:
			trigger.connect()
		self.Game.sendSignal("HeroPowerAcquired", self.ID, self, None, 0, "")
		self.Game.ManaHandler.calcMana_Powers()
		
	def disappears(self):
		for trigger in self.triggersonBoard:
			trigger.disconnect()
		for manaMod in self.manaModifications:
			manaMod.getsRemoved()
		self.manaModifications = []
		
	def replaceHeroPower(self):
		if self.Game.heroPowers[self.ID] != None:
			self.Game.heroPowers[self.ID].disappears()
			self.Game.heroPowers[self.ID] = None
		self.Game.heroPowers[self.ID] = self
		self.appears()
		
	def available(self, choice=0):
		if self.heroPowerTimes >= self.heroPowerChances_base + self.heroPowerChances_extra:
			return False
		if self.needTarget(choice) and self.returnTargets("", choice) == []:
			return False
		return True
		
	def targetCorrect(self, target, choice=0):
		if (target.cardType == "Hero" or target.cardType == "Minion") and target.onBoard:
			return True
		return True
		
	def use(self, target=None, choice=0):
		canUseHeroPower = False
		if self.Game.ManaHandler.costAffordable(self) == False:
			print("Not enough mana to use the Hero Power", self.name)
		else:
			if self.available(choice) and self.selectionLegit(target, choice):
				canUseHeroPower = True
			else:
				print("Invalid selection to use Hero Power %s on target"%self.name, target, ", with choice", choice)
				
		if canUseHeroPower:
			print("	   *********\nHandling using Hero Power %s with target "%self.name, target, ", with choice: ", choice, "\n	   *********")
			#支付费用，清除费用状态。
			self.Game.ManaHandler.payManaCost(self, self.mana)
			#如果有指向，则触发指向扳机（目前只有市长）
			self.Game.target = target
			self.Game.sendSignal("HeroPowerTargetDecision", self.ID, self, target, 0, "", choice)
			minionsKilled = 0
			if self.Game.target != None and self.Game.target.cardType == "Minion" and self.Game.playerStatus[self.ID]["Hero Power Target Adjacent Minions"] > 0:
				targets = self.Game.findAdjacentMinions(target)[0]
				minionsKilled += self.effect(target, choice)
				if targets != []:
					print(self.name, " will also be cast upon minions adjacent to the target minion ", target.name)
					for minion in targets:
						minionsKilled += self.effect(minion, choice)
			else:
				minionsKilled += self.effect(self.Game.target, choice)
				
			#结算阶段结束，处理死亡，此时尚不进行胜负判定。
			#假设触发英雄技能消灭随从的扳机在死亡结算开始之前进行结算。（可能不对，但是相对比较符合逻辑。）
			if minionsKilled > 0:
				self.Game.sendSignal("HeroPowerKilledMinion", self.Game.turn, self, None, minionsKilled, "")
			self.Game.gathertheDead()
			print("Hero used ability: ", self.name)
			self.heroPowerTimes += 1
			#激励阶段，触发“每当你使用一次英雄技能”的扳机，如激励，虚空形态的技能刷新等。
			self.Game.sendSignal("HeroUsedAbility", self.ID, self, self.Game.target, self.mana, "", choice)
			#激励阶段结束，处理死亡。此时可以进行胜负判定。
			self.Game.gathertheDead(True)
			for card in self.Game.Hand_Deck.hands[1] + self.Game.Hand_Deck.hands[2]:
				card.effectCanTrigger()
				card.checkEvanescent()
				
	def effect(self, target, choice=0):
		return 0
		
	def restoresHealth(self, target, heal):
		if self.Game.playerStatus[self.ID]["Heal to Damage"] > 0:
			print("Player's Hero Power healing does damage instead.")
			objtoTakeDamage, targetSurvival = self.dealsDamage(target, heal)
			if targetSurvival > 0:
				self.Game.CounterHandler.damageDealtbyHeroPower[self.ID] += heal
			return objtoTakeDamage, targetSurvival
		else:
			print("Player's Hero Power restores Health to target", target.name)
			heal, targetSurvival = target.getsHealed(self, heal)
			return target, targetSurvival
			
	def dealsDamage(self, target, damage):
		objtoTakeDamage = self.Game.DamageHandler.damageTransfer(target)
		targetSurvival = objtoTakeDamage.damageRequest(self, damage)
		if targetSurvival > 0:
			damageActual, survival = objtoTakeDamage.takesDamage(self, damage)
			self.Game.CounterHandler.damageDealtbyHeroPower[self.ID] += damage
			self.tryLifesteal(damage)
			if targetSurvival > 1: #假设英雄技能消灭一个随从在英雄
				self.Game.sendSignal("HeroPowerKillsMinion", self.ID, self, objtoTakeDamage, 0, "")
		return objtoTakeDamage, targetSurvival
		
	#There are no abilities with AOE healing right now.
	#Whenever you hero power kills minion. Don't know if it triggers after the deathrattle
	#There are currently no Hero Powers that responds to dealing damage, except Frost Lich Jaina's.
	def dealsAOE(self, targets_Damage, damages):
		targets_Damage, damages = fixedList(targets_Damage), fixedList(damages)
		targets_damaged, damagesConnected, targets_Healed, healsConnected = self.Game.AOE_preprocess(self, targets_Damage, damages)
		targets_damaged, damagesActual, targets_Healed, healsActual, totalDamageDone, totalHealingDone, damageSurvivals = self.Game.AOE(self, targets, damagesDone)
		self.Game.CounterHandler.damageDealtbyHeroPower[self.ID] += totalDamageDone
		self.tryLifesteal(totalDamageDone)
		
		for target, survival in zip(targets_damaged, damageSurvivals):
			if survival > 1:
				self.Game.sendSignal("HeroPowerKillsMinion", self.ID, self, target, 0, "")
		return targets_damaged, damagesActual, damageSurvivals
		
	def countDamageDouble(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			if minion.marks["Hero Power Double Heal and Damage"] > 0:
				num += 1
				
		return num
		
	def countHealDouble(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			if minion.marks["Double Heal"] > 0 or minion.marks["Hero Power Double Heal and Damage"] > 0:
				num += 1
				
		return num
		
class SteadyShot(HeroPower):
	name, needTarget = "Steady Shot", False
	index = "Hunter-2-Hero Power-Steady Shot"
	description = "Deal 2 damage to the enemy hero"
	def returnFalse(self, choice=0):
		return self.Game.playerStatus[self.ID]["Hunter Hero Powers Can Target Minions"] > 0
		
	def targetCorrect(self, target, choice=0):
		if self.Game.playerStatus[self.ID]["Hunter Hero Powers Can Target Minions"] > 0:
			return (target.cardType == "Minion" or target.cardType == "Hero") and target.onBoard
		else:
			return target.cardType == "Hero" and target.ID != self.ID and target.onBoard
			
	def effect(self, target=None, choice=0):
		damage = (2 + self.Game.playerStatus[self.ID]["Hero Power Damage Boost"]) * (2 ** self.countDamageDouble())
		if target != None:
			print("Hero Power Steady Shot deals %d damage to the character"%damage, target.name)
			self.dealsDamage(target, damage)
		else:
			print("Hero Power Steady Shot deals %d damage to the enemy hero"%damage, self.Game.heroes[3-self.ID].name)
			self.dealsDamage(self.Game.heroes[3-self.ID], damage)
		return 0
		
		
class Hero(Card):
	mana, weapon, description = 0, None, ""
	Class, name, heroPower, armor = "Neutral", "InnKeeper", SteadyShot, 0
	index = ""
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.mana, self.manaModifications = type(self).mana, []
		self.health_upper, self.health = 30, 30
		self.attack, self.attack_bare, self.armor = 0, 0, type(self).armor
		self.name = type(self).name
		self.index = type(self).index
		self.cardType = "Hero"
		self.weapon = type(self).weapon
		self.description = type(self).description
		self.Class = type(self).Class
		self.attChances_base, self.attChances_extra, self.attTimes = 1, 0, 0
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.dead = False
		self.heroPower = type(self).heroPower(self.Game, self.ID)
		self.keyWords = {"Poisonous": 0} #Just as a placeholder
		self.status = {"Frozen": 0, "Temp Stealth": 0}
		self.identity = [np.random.rand(), np.random.rand()]
		self.options = [] #For Choose One heroes
		self.overload, self.chooseOne = 0, 0
		self.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.evanescent = False
		
	"""Handle hero's attacks, attack chances, attack chances and frozen status."""
	def statusPrint(self):
		#print("Hero name: ", self.name, " onBoard: ", self.onBoard, " inHand: ", self.inHand, " inDeck: ", self.inDeck)
		print("Hero ", self.name, ": Attacked times : %d.	Base attack chances left: %d.	Extra attack chances left: "%(self.attTimes, self.attChances_base), self.attChances_extra)
		print("Hero ", self.name, " is frozen: ", self.status["Frozen"], " has Temp Stealth: ", self.status["Temp Stealth"])
		print("Player status: ")
		for key, value in self.Game.playerStatus[self.ID].items():
			if value > 0:
				print(key, ": ", value)
				
	def actionable(self):
		if self.ID == self.Game.turn:
			#不考虑冻结、零攻和自身有不能攻击的debuff的情况。
			return True
		return False
		
	def decideAttChances_base(self):
		weapon = self.Game.availableWeapon(self.ID)
		if weapon != None and weapon.keyWords["Windfury"] > 0:
			self.attChances_base = 2
		else:
			self.attChances_base = 1
			
	def getsFrozen(self):
		self.status["Frozen"] += 1
		print(self.name, "gets Frozen.")
		
	def turnStarts(self, ID):
		if ID == self.ID:
			self.status["Temp Stealth"] = 0
			if self.Game.playerStatus[self.ID]["ImmuneTillYourNextTurn"] > 0:
				self.Game.playerStatus[self.ID]["Immune"] -= self.Game.playerStatus[self.ID]["ImmuneTillYourNextTurn"]
				self.Game.playerStatus[self.ID]["Immune"] = max(0, self.Game.playerStatus[self.ID]["Immune"])
				self.Game.playerStatus[self.ID]["ImmuneTillYourNextTurn"] = 0
			if self.Game.playerStatus[self.ID]["EvasiveTillYourNextTurn"] > 0:
				self.Game.playerStatus[self.ID]["Evasive"] -= self.Game.playerStatus[self.ID]["EvasiveTillYourNextTurn"]
				self.Game.playerStatus[self.ID]["Evasive"] = max(0, self.Game.playerStatus[self.ID]["Evasive"])
				
			weapon = self.Game.availableWeapon(self.ID)
			self.bareAttack, self.attTimes, self.attChances_extra = 0, 0, 0
			if weapon != None:
				self.attack = self.bareAttack + max(0, weapon.attack)
				print("Hero %s's attack is now %d+%d"%(self.name, self.bareAttack, weapon.attack))
			self.decideAttChances_base()
			
	def turnEnds(self, ID):
		if self.Game.playerStatus[self.ID]["ImmuneTillEndofTurn"] > 0:
			self.Game.playerStatus[self.ID]["Immune"] -= self.Game.playerStatus[self.ID]["ImmuneTillEndofTurn"]
			self.Game.playerStatus[self.ID]["Immune"] = max(0, self.Game.playerStatus[self.ID]["Immune"])
			self.Game.playerStatus[self.ID]["ImmuneTillEndofTurn"] = 0
			
		if ID == self.ID:
			#一个角色只有在自己的回合结束时才能解冻
			if self.status["Frozen"] > 0 and self.attChances_base + self.attChances_extra > self.attTimes:
				self.status["Frozen"] = 0
				
			self.attack, self.attack_bare = 0, 0 #因为英雄没有跨回合的攻击力增加，所有攻击增益都会在回合结束时消失。
			self.attTimes = 0
			
	def gainTempAttack(self, attackGain):
		self.attack_bare += attackGain
		weapon = self.Game.availableWeapon(self.ID)
		if weapon != None:
			self.attack = self.attack_bare + max(0, weapon.attack)
		else:
			self.attack = self.attack_bare
			
	def gainsArmor(self, armor):
		self.armor += armor
		
	"""Handle hero's being selectable by subjects or not. And hero's availability for battle."""
	def selectablebySpellandHeroPower(self, subject):
		if self.onBoard and self.Game.playerStatus[self.ID]["Evasive"] < 1:
			if self.ID == subject.ID:
				return True
			else:
				if self.status["Temp Stealth"] + self.Game.playerStatus[self.ID]["Immune"] < 1:
					return True
		return False
		
	def selectablebyBattle(self, subject):
		if self.onBoard and self.ID != subject.ID and self.status["Temp Stealth"] + self.Game.playerStatus[self.ID]["Immune"] < 1:
			for minion in self.Game.minionsonBoard(self.ID):
				if minion.keyWords["Taunt"] > 0 and minion.selectablebyBattle(subject):
					print(self.name, " is behind friendly Taunt minions and can't be attacked first.")
					return False
			return True
		print(self.name, " is a friendly or has Stealth or Immune.")
		return False
		
	def selectablebyBattlecry(self, subject):
		if self.onBoard:
			if self.ID == subject.ID:
				return True
			else:
				if self.status["Temp Stealth"] + self.Game.playerStatus[self.ID]["Immune"] < 1:
					return True
		return False
			
	def canAttack(self):
		if self.actionable() == False or self.attack < 1 or self.status["Frozen"] > 0:
			return False
		if self.attChances_base + self.attChances_extra <= self.attTimes:
			return False
		return True
		
	def canAttackTarget(self, target):
		if self.canAttack() == False:
			return False
		if target.selectablebyBattle(self) == False:
			return False
		return True
		
	#Heroes don't have Lifesteal.
	def tryLifesteal(self, damage):
		pass
		
	def damageRequest(self, subject, damage):
		if damage <= 0 or self.Game.playerStatus[self.ID]["Immune"] > 0:
			return 0
		else:
			if self.Game.playerStatus[self.ID]["Hero Takes 1 Damage at a Time"] > 0:
				damage = 1
				
			if damage > self.health + self.armor:
				return 3 #Overkilled
			elif damage == self.health + self.armor:
				return 2 #Killed exactly.
			else:
				return 1 #Survives damage.
				
	#This function will only be invoked when damage > 0
	def takesDamage(self, subject, damage, sendDamageSignal=True):
		if self.Game.playerStatus[self.ID]["Hero Takes 1 Damage at a Time"] > 0 and damage > 0:
			damage = 1
			
		survival = 0
		if self.armor > damage:
			self.armor -= damage
			survival = 1
		else:
			self.health -= damage - self.armor
			self.armor = 0
			if self.health > 0:
				survival = 1
			elif self.health == 0:
				survival = 2
			else:
				survival = 3
				
		if survival > 0:
			print("Hero %s takes %d damage"%(self.name, damage))
			self.Game.CounterHandler.damageonHeroThisTurn[self.ID] += damage
			if sendDamageSignal:
				self.Game.sendSignal("HeroTakesDamage", self.ID, subject, self, damage, "")
				self.Game.sendSignal("HeroTookDamage", self.ID, subject, self, damage, "")
				
		return damage, survival
		
	def getsHealed(self, subject, heal, sendHealSignal=True):
		if self.health == self.health_upper:
			print("Hero at full health already.")
			return 0, 0 #healDone is 0, survival status is 0
		else:
			if self.health < self.health_upper - heal:
				self.health += heal
				self.Game.CounterHandler.healthRestoredThisGame[subject.ID] += heal
				if sendHealSignal:
					self.Game.sendSignal("HeroGetsHealed", self.Game.turn, subject, self, heal, "StillDamaged")
				return heal, -1
			else:
				healDone = self.health_upper - self.health
				self.Game.CounterHandler.healthRestoredThisGame[subject.ID] += healDone
				self.health = self.health_upper
				if sendHealSignal:
					self.Game.sendSignal("HeroGetsHealed", self.Game.turn, subject, self, healDone, "FullyHealed")
				return healDone, -2
				
	#专门被英雄牌使用，加拉克苏斯大王和拉格纳罗斯都不会调用该方法。
	def played(self, choice=0, mana=0): #英雄牌使用不存在触发发现的情况
	#使用阶段
		#英雄牌替换出的英雄的生命值，护甲和攻击机会都会继承当前英雄的值。
		self.health = self.Game.heroes[self.ID].health
		self.health_upper = self.Game.heroes[self.ID].health_upper
		self.armor = self.Game.heroes[self.ID].armor
		self.attack_bare = self.Game.heroes[self.ID].attack_bare
		self.attTimes = self.Game.heroes[self.ID].attTimes
		#英雄牌进入战场。（本来是应该在使用阶段临近结束时移除旧英雄和旧技能，但是为了方便，在此时执行。）
		#继承旧英雄的生命状态和护甲值。此时英雄的被冻结和攻击次数以及攻击机会也继承旧英雄。
		#清除旧的英雄技能。
		self.Game.heroPowers[self.ID].disappears()
		self.Game.heroPowers[self.ID].heroPower = None
		self.Game.heroes[self.ID].onBoard = False
		heroPower = self.heroPower #这个英雄技能必须存放起来，之后英雄还有可能被其他英雄替换，但是这个技能要到最后才登场。
		self.Game.heroes[self.ID] = self #英雄替换。如果后续有埃克索图斯再次替换英雄，则最后的英雄是拉格纳罗斯。
		self.Game.heroes[self.ID].onBoard = True
		#使用时步骤，触发“每当你使用一张xx牌时”的扳机。
		self.Game.sendSignal("HeroCardPlayed", self.ID, self, None, mana, "", choice)
		#英雄牌的最大生命值和现有生命值以及护甲被设定继承旧英雄的数值。并获得英雄牌上标注的护甲值。
		self.gainsArmor(type(self).armor)
		#使用阶段结束，进行死亡结算，此时尚不进行胜负判定。
		self.Game.gathertheDead()
	#结算阶段
		#获得新的英雄技能。注意，在此之前英雄有可能被其他英雄代替，如伊利丹飞刀打死我方的管理者埃克索图斯。
			#埃克索图斯可以替换英雄和英雄技能，然后本英雄牌在此处开始结算，再次替换英雄技能为正确的英雄牌技能。
		heroPower.replaceHeroPower()
		#视铜须等的存在而结算战吼次数以及具体战吼。
		#不用返回主体，但是当沙德沃克调用时whenEffective函数的时候需要。
		if self.Game.playerStatus[self.ID]["Battlecry Trigger Twice"] > 0:
			self.whenEffective(None, "", choice)
		self.whenEffective(None, "", choice)
		if self.weapon != None: #如果英雄牌本身带有武器，如迦拉克隆等。则装备那把武器
			self.Game.equipWeapon(self.weapon(self.Game, self.ID))
		weapon = self.Game.availableWeapon(self.ID)
		if weapon != None and self.ID == self.Game.turn:
			self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare + max(0, weapon.attack)
		else:
			self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare
		self.Game.heroes[self.ID].decideAttChances_base()
		#结算阶段结束，处理死亡，此时尚不进行胜负判定。
		self.Game.gathertheDead()
		
	#大王，炎魔之王拉格纳罗斯等替换英雄，此时没有战吼。
	#炎魔之王变身不会摧毁玩家的现有装备和奥秘。只会移除冰冻，免疫和潜行等状态。
	def replaceHero(self, fromHeroCard=False):
		#英雄被替换
		#被替换的英雄失去所有护甲。
		#假设直接替换的英雄不会继承之前英雄获得的回合内攻击力增加。
		self.attTimes = self.Game.heroes[self.ID].attTimes
		#英雄牌进入战场。（本来是应该在使用阶段临近结束时移除旧英雄和旧技能，但是为了方便，在此时执行。）
		#继承旧英雄的生命状态和护甲值。此时英雄的被冻结和攻击次数以及攻击机会也继承旧英雄。
		#大王和炎魔之王在替换之前被定义，拥有15或者8点生命值。0点护甲值和英雄技能等也已定义完毕。
		self.Game.heroes[self.ID] = self
		self.Game.heroes[self.ID].onBoard = True
		self.heroPower.replaceHeroPower()
		if self.weapon != None: #如果英雄本身带有装备，则会替换当前的玩家装备（如加拉克苏斯大王）
			self.Game.equipWeapon(self.weapon(self.Game, self.ID))
		if fromHeroCard == False: #英雄牌被其他牌打出时不会取消当前玩家的免疫状态
			self.Game.playerStatus[self.ID]["ImmuneTillEndofTurn"] = 0
			self.Game.playerStatus[self.ID]["ImmuneTillYourNextTurn"] = 0
			self.Game.playerStatus[self.ID]["Immune"] = 0 #Hero's immune state is gone, except that given by Mal'Ganis
		self.Game.sendSignal("HeroReplaced", self.ID, None, self, 0, "")
		
		
		
		
class Weapon(Card):
	Class, name, description = "Neutral", "Vanilla", ""
	mana, attack, durability = 2, 2, 2
	index = "Vanillar-Neutral-2-2-2-Weapon-Vanilla"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		
	def blank_init(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.Class, self.name = type(self).Class, type(self).name
		self.cardType = "Weapon"
		self.mana, self.manaModifications = type(self).mana, []
		self.attack = type(self).attack
		self.stat_AuraAffected = [0, []] #没有针对武器耐久度的光环
		self.durability = type(self).durability #将来会处理有buff的武器洗入牌库的问题，如弑君
		self.description = type(self).description
		self.needTarget = False
		self.keyWords = {"Lifesteal": False, "Poisonous": False, "Windfury": False}
		self.marks = {"Attack Adjacent Minions": 0}
		self.overload, self.chooseOne = 0, 0
		self.onBoard, self.inHand, self.inDeck = False, False, False
		self.tobeDestroyed = False
		self.sequence = -1
		self.deathrattles = []
		self.triggersonBoard, self.triggersinHand, self.triggersinDeck = [], [], []
		self.identity = [np.random.rand(), np.random.rand(), np.random.rand()]
		self.options = [] #For Choose One weapon, non-existent at this point.
		self.auras = {}
		self.evanescent = True
		
	def statusPrint(self):
		print("Weapon: %s. Description:"%self.name, self.description)
		#print("Weapon onBoard: ", self.onBoard, " inHand: ", self.inHand, " inDeck:", self.inDeck)
		if self.triggersonBoard != []:
			print("Weapon's triggersonBoard")
			for trigger in self.triggersonBoard:
				print(type(trigger))
		#if self.triggersinHand != []:
		#	print("Weapon's triggersinHand")
		#	for trigger in self.triggersinHand:
		#		print(type(trigger))
		#		
	"""Handle weapon entering/leaving board/hand/deck"""
	#武器进场并连接侦听器，比如公正之剑可以触发伊利丹的召唤，这个召唤又反过来触发公正之剑的buff效果。
	def appears(self):
		#注意，此时武器还不能设为onBoard,因为之后可能会涉及亡语随从为英雄装备武器。
		#尚不能因为武器标记为onBoard而调用其destroyed。
		self.inHand, self.inDeck, self.tobeDestroyed = False, False, False
		self.mana = type(self).mana
		#武器的表面上的场上扳机和亡语都有相同的入场注册方式
		for trigger in self.triggersonBoard:
			trigger.connect() #把(obj, signal)放入Game.triggersonBoard中
		for trigger in self.deathrattles:
			trigger.connect()
		for value in self.auras.values(): #目前似乎只用舔舔魔杖有武器光环
			print("Now starting weapon %s's Aura", value)
			value.auraAppears()
			
	def setasNewWeapon(self):
		self.onBoard, self.tobeDestroyed = True, False
		self.sequence = len(self.Game.minions[1]) + len(self.Game.minions[2]) + len(self.Game.weapons[1]) + len(self.Game.weapons[2])
		self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare + max(0, self.attack)
		self.Game.heroes[self.ID].decideAttChances_base()
		self.Game.sendSignal("WeaponEquipped", self.ID, self, None, 0, "")
		
	#Take care of the hero's attack chances and attack.
	#The deathrattles will be left to gathertheDead() and deathHandle()
	def destroyed(self):
		if self.onBoard: #只有装备着的武器才会触发，以防连续触发。
			print("Weapon %s is destroyed"%self.name)
			if self.keyWords["Windfury"] > 0:
				self.Game.heroes[self.ID].decideAttChances_base()
			self.onBoard, self.tobeDestroyed = False, True
			self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare
			#移除武器对应的场上扳机，亡语扳机在deathrattles中保存
			for trigger in self.triggersonBoard:
				trigger.disconnect()
				
			for value in self.auras.values():
				value.auraDisappears()
			#self.Game.sendSignal("WeaponRemoved", self.ID, self, None, 0, "")
			
	def deathResolution(self, attackbeforeDeath, triggersAllowed_WhenDies, triggersAllowed_AfterDied):
		print("Now resolving the destruction of weapon", self.name)
		#除了武器亡语以外，目前只有一个应对武器被摧毁的扳机，即冰封王座的Grave Shambler
		self.Game.sendSignal("WeaponDestroyed", self.ID, None, self, 0, "", triggersAllowed_WhenDies)
		self.Game.sendSignal("WeaponRemoved", self.ID, None, self, 0, "")
		for trigger in self.deathrattles:
			trigger.disconnect()
		self.__init__(self.Game, self.ID)
		
	def disappears(self):
		if self.onBoard: #只有装备着的武器才会触发，以防连续触发。
			print("Weapon %s leaves board"%self.name)
			if self.keyWords["Windfury"] > 0:
				self.Game.heroes[self.ID].decideAttChances_base()
			self.onBoard = False
			self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare
			#移除武器对应的场上扳机，亡语扳机在deathrattles中保存
			for trigger in self.triggersonBoard:
				trigger.disconnect()
			for value in self.auras.values():
				value.auraDisappears()
			self.Game.sendSignal("WeaponRemoved", self.ID, self, None, 0, "")
			
	"""Handle the mana, durability and stat of weapon."""
	#This method is invoked by Hero class, not a listner.			
	def loseDurability(self):
		print("Weapon %s loses 1 Durability"%self.name)
		self.durability -= 1
		
	def gainStat(self, attack, durability):
		self.attack += attack
		self.durability += durability
		if self.Game.turn == self.ID:
			self.Game.heroes[self.ID].attack = self.Game.heroes[self.ID].attack_bare + max(0, self.attack)
			
	"""Handle the weapon being played/equipped."""
	def played(self, target=None, comment=""):
	#使用阶段
		#武器进场并连接侦听器，比如公正之剑可以触发伊利丹的召唤，这个召唤又反过来触发公正之剑的buff效果。
		self.Game.weapons[self.ID].append(self)
		self.appears() #此时可以建立侦听器。此时onBoard还是False
		#注意，暂时不取消已经装备的武器的侦听，比如两把公正之剑可能同时为伊利丹召唤的元素buff。
		#使用时步骤，触发“每当你使用一张xx牌”的扳机，如伊利丹和无羁元素。
		self.Game.sendSignal("WeaponPlayed", self.ID, self, target, 0, "", choice=0)
		#结算过载。
		if self.overload > 0:
			print(self.name, " is played and Overloads %d mana crystals."%self.overload)
			self.Game.ManaHandler.overloadMana(self.overload, self.ID)
		#使用阶段结束，处理亡语，暂不处理胜负问题。
		#注意，如果此时伊利丹飞刀造成了我方佛丁的死亡，则其装备的灰烬使者会先替换目前装备的武器。
		#之后在结算阶段的武器正式替换阶段，被替换的武器就变成了灰烬使者。最终装备的武器依然是打出的这把武器。
		self.Game.gathertheDead() #此时被替换的武器先不视为死亡，除非被亡语引起的死亡结算先行替换（如佛丁）。
	#结算阶段
		#根据市长的存在情况来决定随机目标。
		self.Game.target = target
		self.Game.sendSignal("BattlecryTargetDecision", self.ID, self, target, 0, "", choice=0)
		target = self.Game.target
		#根据铜须的存在情况来决定战吼的触发次数。不同于随从，武器的连击目前不会触发
		if self.Game.playerStatus[self.ID]["Battlecry Trigger Twice"] > 0:
			#对方武器而言没有必要返回主体对象，但是当战吼被沙德沃克调用的时候，需要返回。
			target = self.whenEffective(target, 0)
		target = self.whenEffective(target, 0)
		#消灭旧武器，并将列表前方的武器全部移除。
		
		for weapon in self.Game.weapons[self.ID]:
			if weapon != self:
				#The removal of the preivous weapons will be left to the gathertheDead() method.
				#只有标记为onBoard的武器调用destroyed会有反应，防止因为之前佛丁的死亡引起同一把武器的多次摧毁信号。
				weapon.destroyed() #触发“每当你的一把武器被摧毁时”和“每当你的一把武器离场时”的扳机，如南海船工。
		#打出的这把武器会成为最后唯一还装备着的武器。触发“每当你装备一把武器时”的扳机，如锈水海盗。
		self.setasNewWeapon() #此时打出的武器的onBoard才会正式标记为True
		print("Weapon %s is now onBoard:"%self.name, self.onBoard)
				
		#结算阶段结束，处理亡语。（此时的亡语结算会包括武器的亡语结算。）
		self.Game.gathertheDead()
		#完成阶段在Game.playWeapon中处理。
		
	"""Handle the weapon restoring health, dealing damage and dealing AOE effects."""
	#对于武器而言，dealsDamage()只有毁灭之刃可以使用，因为其他的武器造成伤害不是AOE伤害就是战斗伤害
	#战斗伤害会在随从和英雄的attacks()方法中统一处理。毁灭之刃是唯一的拥有单体战吼的武器。
	
	def countHealDouble(self):
		num = 0
		for minion in self.Game.minions[self.ID]:
			if minion.marks["Double Heal"]:
				num += 1
		return num
		
		