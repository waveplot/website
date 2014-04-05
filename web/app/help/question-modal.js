
function QuestionModalController($scope, $modalInstance, question){
    $scope.question = question.question;
    $scope.answer = question.answer;

    var d = new Date(question.answered);
    $scope.footer_string = d.toISOString().substr(0,10);

    $scope.ok = function () {
        $modalInstance.close();
    };
}
