
function QuestionModalController($scope, $modalInstance, question, answer){
    $scope.question = question;
    $scope.answer = answer;
    
    $scope.ok = function () {
        $modalInstance.close();
    };
};
