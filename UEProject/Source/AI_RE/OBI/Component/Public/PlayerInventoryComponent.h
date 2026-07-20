// Copyright MixUpProject. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PlayerInventoryComponent.generated.h"

USTRUCT(BlueprintType)
struct FInventoryItemStack
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, EditAnywhere)
	int32 SlotIndex = -1;

	UPROPERTY(BlueprintReadWrite, EditAnywhere)
	FName ItemId;

	UPROPERTY(BlueprintReadWrite, EditAnywhere)
	int32 Count = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FInventoryChangedSignature);

UCLASS(ClassGroup = (Player), meta = (BlueprintSpawnableComponent))
class AI_RE_API UPlayerInventoryComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPlayerInventoryComponent();

	UPROPERTY(BlueprintAssignable, Category = "Inventory|Events")
	FInventoryChangedSignature OnInventoryChanged;

	UFUNCTION(BlueprintCallable, Category = "Inventory")
	bool AddItem(FName ItemId, int32 Count);

	UFUNCTION(BlueprintCallable, Category = "Inventory")
	bool ConsumeItem(FName ItemId, int32 Count);

	UFUNCTION(BlueprintCallable, Category = "Inventory")
	bool MoveItemSlot(int32 FromSlotIndex, int32 ToSlotIndex);

	UFUNCTION(BlueprintCallable, Category = "Inventory")
	bool DropItemFromSlot(int32 SlotIndex, int32 Count);

	UFUNCTION(BlueprintPure, Category = "Inventory")
	int32 GetItemCount(FName ItemId) const;

	UFUNCTION(BlueprintPure, Category = "Inventory")
	bool IsInventoryFull() const;

	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	int32 MaxSlots = 30;

	UPROPERTY(BlueprintReadOnly, Category = "Inventory")
	TArray<FInventoryItemStack> Items;

protected:
	virtual void BeginPlay() override;

	FInventoryItemStack* FindStackBySlot(int32 SlotIndex);
	int32 FindFirstEmptySlotIndex() const;
	int32 GetMaxStackForItem(FName ItemId) const;
};
